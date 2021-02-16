##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################

import pytest

from idaes.core import FlowsheetBlock
from idaes.generic_models.properties.core.eos.ceos import \
    cubic_roots_available
from idaes.power_generation.properties.natural_gas_PR import get_NG_properties
from idaes.generic_models.properties.core.generic.generic_property import (
        GenericParameterBlock)
from idaes.generic_models.unit_models import GibbsReactor
from pyomo.util.check_units import assert_units_consistent

from pyomo.environ import (ConcreteModel,
                           Objective,
                           SolverFactory,
                           SolverStatus,
                           TerminationCondition,
                           value)

from idaes.core.util.testing import get_default_solver

import idaes.logger as idaeslog
SOUT = idaeslog.INFO

# Set module level pyest marker
pytestmark = pytest.mark.cubic_root
prop_available = cubic_roots_available()

# Get default solver for testing
solver = get_default_solver()


class TestNaturalGasProps(object):
    @pytest.fixture()
    def m(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={'dynamic': False})

        m.fs.props = GenericParameterBlock(default=get_NG_properties())
        m.fs.state = m.fs.props.build_state_block(
                [1],
                default={"defined_state": True})

        return m

    @pytest.mark.integration
    def test_T_sweep(self, m):
        assert_units_consistent(m)

        m.fs.obj = Objective(expr=(m.fs.state[1].temperature - 510)**2)

        for logP in range(8, 13, 1):
            m.fs.obj.deactivate()

            m.fs.state[1].flow_mol.fix(100)
            m.fs.state[1].mole_frac_comp["H2"].fix(0.1)
            m.fs.state[1].mole_frac_comp["CO"].fix(0.1)
            m.fs.state[1].mole_frac_comp["H2O"].fix(0.1)
            m.fs.state[1].mole_frac_comp["CO2"].fix(0.1)
            m.fs.state[1].mole_frac_comp["O2"].fix(0.1)
            m.fs.state[1].mole_frac_comp["N2"].fix(0.1)
            m.fs.state[1].mole_frac_comp["Ar"].fix(0.1)
            m.fs.state[1].mole_frac_comp["CH4"].fix(0.1)
            m.fs.state[1].mole_frac_comp["C2H6"].fix(0.1)
            m.fs.state[1].mole_frac_comp["C3H8"].fix(0.05)
            m.fs.state[1].mole_frac_comp["C4H10"].fix(0.05)
            m.fs.state[1].temperature.fix(300)
            m.fs.state[1].pressure.fix(10**(0.5*logP))

            m.fs.state.initialize(outlvl=0)

            m.fs.state[1].temperature.unfix()
            m.fs.obj.activate()

            solver = SolverFactory('ipopt')
            results = solver.solve(m, tee=True)

            assert results.solver.termination_condition == \
                TerminationCondition.optimal

    @pytest.mark.integration
    def test_P_sweep(self, m):
        for T in range(370, 1000, 25):
            m.fs.state[1].flow_mol.fix(100)
            m.fs.state[1].mole_frac_comp["H2"].fix(0.1)
            m.fs.state[1].mole_frac_comp["CO"].fix(0.1)
            m.fs.state[1].mole_frac_comp["H2O"].fix(0.1)
            m.fs.state[1].mole_frac_comp["CO2"].fix(0.1)
            m.fs.state[1].mole_frac_comp["O2"].fix(0.1)
            m.fs.state[1].mole_frac_comp["N2"].fix(0.1)
            m.fs.state[1].mole_frac_comp["Ar"].fix(0.1)
            m.fs.state[1].mole_frac_comp["CH4"].fix(0.1)
            m.fs.state[1].mole_frac_comp["C2H6"].fix(0.1)
            m.fs.state[1].mole_frac_comp["C3H8"].fix(0.05)
            m.fs.state[1].mole_frac_comp["C4H10"].fix(0.05)
            m.fs.state[1].temperature.fix(T)
            m.fs.state[1].pressure.fix(1e5)

            m.fs.state.initialize(outlvl=0)

            solver = SolverFactory('ipopt')
            results = solver.solve(m)

            assert results.solver.termination_condition == \
                TerminationCondition.optimal

            while m.fs.state[1].pressure.value <= 1e6:
                m.fs.state[1].pressure.value = (
                    m.fs.state[1].pressure.value + 1e5)
                solver = SolverFactory('ipopt')
                results = solver.solve(m)
                assert results.solver.termination_condition == \
                    TerminationCondition.optimal

    @pytest.mark.component
    def test_gibbs(self, m):
        m.fs.props = GenericParameterBlock(
            default=get_NG_properties(components=['H2', 'CO', 'H2O', 'CO2',
                                                  'O2', 'N2', 'Ar', 'CH4']))
        m.fs.reactor = GibbsReactor(default={
            "dynamic": False,
            "has_heat_transfer": True,
            "has_pressure_change": False,
            "property_package": m.fs.props})

        m.fs.reactor.inlet.flow_mol.fix(8000)  # mol/s
        m.fs.reactor.inlet.temperature.fix(600)  # K
        m.fs.reactor.inlet.pressure.fix(1e6)  # Pa

        m.fs.reactor.outlet.temperature.fix(600)  # K

        m.fs.reactor.inlet.mole_frac_comp[0, "H2"].fix(0)
        m.fs.reactor.inlet.mole_frac_comp[0, "CO"].fix(0)
        m.fs.reactor.inlet.mole_frac_comp[0, "H2O"].fix(0.3)
        m.fs.reactor.inlet.mole_frac_comp[0, "CO2"].fix(0)
        m.fs.reactor.inlet.mole_frac_comp[0, "O2"].fix(0.2)
        m.fs.reactor.inlet.mole_frac_comp[0, "N2"].fix(0.05)
        m.fs.reactor.inlet.mole_frac_comp[0, "Ar"].fix(0.05)
        m.fs.reactor.inlet.mole_frac_comp[0, "CH4"].fix(0.4)

        solver = SolverFactory('ipopt')
        results = solver.solve(m, tee=True)

        assert results.solver.termination_condition == \
            TerminationCondition.optimal
        assert results.solver.status == SolverStatus.ok

        assert 0.017 == pytest.approx(value(
            m.fs.reactor.outlet.mole_frac_comp[0, 'H2']), 1e-1)
        assert 0.0001 == pytest.approx(value(
            m.fs.reactor.outlet.mole_frac_comp[0, 'CO']), 1)
        assert 0.487 == pytest.approx(value(
            m.fs.reactor.outlet.mole_frac_comp[0, 'H2O']), 1e-1)
        assert 0.103 == pytest.approx(value(
            m.fs.reactor.outlet.mole_frac_comp[0, 'CO2']), 1e-1)
        assert 0.293 == pytest.approx(value(
            m.fs.reactor.outlet.mole_frac_comp[0, 'CH4']), 1e-1)

        assert -634e6 == pytest.approx(value(
            m.fs.reactor.heat_duty[0]), 1e-3)
