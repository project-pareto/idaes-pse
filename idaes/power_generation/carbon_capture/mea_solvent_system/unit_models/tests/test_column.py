##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2019, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
"""
Author: Paul Akula, Anuja Deshpande
"""
# Import Python libraries
import sys
import os
import pytest

# Import Pyomo libraries
from pyomo.environ import ConcreteModel, value, Param, TransformationFactory,\
    SolverFactory , TerminationCondition, units as pyunits

# Import IDAES Libraries
from idaes.core import FlowsheetBlock
from idaes.core.util.model_statistics import degrees_of_freedom

# Access the mea_solvent_system dir from the current dir (tests dir)
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from unit_models.column import PackedColumn
from properties.vapor_prop import VaporParameterBlock
from properties.liquid_prop import LiquidParameterBlock

# -----------------------------------------------------------------------------
solver = SolverFactory('ipopt')

class TestColumn:
    '''
    Tests for the column model
    '''

    @pytest.fixture(scope="module", params=['Absorber', 'Stripper'])
    def column_model_ss(self, request):

        Fpar = request.param
        # spacial domain finite elemets and finite element list
        x_nfe = 10
        x_nfe_list = [i / x_nfe for i in range(x_nfe + 1)]

        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})
        # Set up property package
        m.fs.vapor_properties = VaporParameterBlock(
            default={'process_type': Fpar})
        m.fs.liquid_properties = LiquidParameterBlock()

        # create instance of column on flowsheet
        m.fs.col = PackedColumn(default={
            "process_type": Fpar,
            "finite_elements": x_nfe,
            "length_domain_set": x_nfe_list,
            "transformation_method": "dae.finite_difference",
            "flow_type": "counter_current",
            "vapor_side": {
                "transformation_scheme": "BACKWARD",
                "property_package": m.fs.vapor_properties,
                "has_pressure_change": False,
                "pressure_drop_type": None},
            "liquid_side":
            {
                "transformation_scheme": "FORWARD",
                "property_package": m.fs.liquid_properties
            }})

        # Fix  input variables
        m.fs.col.dia_col.fix(0.64135)
        if Fpar == 'Absorber':
            m.fs.col.length_col.fix(18.15)
            for t in m.fs.time:
                # vapor
                m.fs.col.vap_in_flow[t].fix(21.48)
                m.fs.col.vap_in_temperature[t].fix(317.88)
                m.fs.col.bot_pressure[t].fix(107650)
                m.fs.col.vap_in_mole_frac[t, "CO2"].fix(0.11453)
                m.fs.col.vap_in_mole_frac[t, "H2O"].fix(0.08526)
                m.fs.col.vap_in_mole_frac[t, "N2"].fix(0.73821)
                m.fs.col.vap_in_mole_frac[t, "O2"].fix(0.06200)
                # liquid
                m.fs.col.liq_in_flow[t].fix(37.55)
                m.fs.col.liq_in_temperature[t].fix(319.87)
                m.fs.col.liq_in_mole_frac[t, "CO2"].fix(0.00963)
                m.fs.col.liq_in_mole_frac[t, "H2O"].fix(0.87435)
                m.fs.col.liq_in_mole_frac[t, "MEA"].fix(0.11602)
                #Stream exit temperature
                m.fs.col.vapor_exit_temp = Param(initialize=346.17684550190495)
                m.fs.col.liquid_exit_temp = Param(initialize=322.95279074281416)
            #initialize column
            m.fs.col.initialize()
        elif Fpar == 'Stripper':
            m.fs.col.length_col.fix(12.1)
            for t in m.fs.time:
                # vapor
                m.fs.col.vap_in_flow[t].fix(17.496)
                m.fs.col.vap_in_temperature[t].fix(396.6)
                m.fs.col.bot_pressure[t].fix(183430)
                m.fs.col.vap_in_mole_frac[t, "CO2"].fix(0.0145)
                m.fs.col.vap_in_mole_frac[t, "H2O"].fix(0.9855)
                # liquid
                m.fs.col.liq_in_flow[t].fix(84.48)
                m.fs.col.liq_in_temperature[t].fix(382.15)
                m.fs.col.liq_in_mole_frac[t, "CO2"].fix(0.0331)
                m.fs.col.liq_in_mole_frac[t, "H2O"].fix(0.8547)
                m.fs.col.liq_in_mole_frac[t, "MEA"].fix(0.1122)
                #Stream exit temperature
                m.fs.col.vapor_exit_temp = Param(initialize=396.79057912844183)
                m.fs.col.liquid_exit_temp = Param(initialize= 393.9197958570096)
            #initialize column
            m.fs.col.initialize(homotopy_steps_h=[0.1, 0.2, 0.4, 0.6, 0.8, 1])
        return m


    @pytest.fixture(scope="module", params=['Absorber', 'Stripper'])
    def column_model_dyn(self, request):

        Fpar = request.param
        # spacial domain finite elemets and finite element list
        x_nfe = 10
        x_nfe_list = [i / x_nfe for i in range(x_nfe + 1)]

        # time horizon
        t_nfe = 2
        time_set = [0, 4]

        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": True,
                                       'time_units': pyunits.s,
                                       "time_set": time_set})
        # Set up property package
        m.fs.vapor_properties = VaporParameterBlock(
            default={'process_type': Fpar})
        m.fs.liquid_properties = LiquidParameterBlock()

        # create instance of column  on flowsheet
        m.fs.col = PackedColumn(default={
            "process_type": Fpar,
            "finite_elements": x_nfe,
            "length_domain_set": x_nfe_list,
            "transformation_method": "dae.finite_difference",
            "flow_type": "counter_current",
            "vapor_side": {
                "transformation_scheme": "BACKWARD",
                "property_package": m.fs.vapor_properties,
                "has_pressure_change": False,
                "pressure_drop_type": None},
            "liquid_side":
            {
                "transformation_scheme": "FORWARD",
                "property_package": m.fs.liquid_properties
            }})

        # Time discretization
        discretizer = TransformationFactory('dae.finite_difference')
        discretizer.apply_to(m.fs, wrt=m.fs.time, nfe=t_nfe, scheme='BACKWARD')

        #fix inputs variables
        m.fs.col.dia_col.fix(0.64135)
        if Fpar == 'Absorber':
            m.fs.col.length_col.fix(18.15)
            for t in m.fs.time:
                # vapor
                m.fs.col.vap_in_flow[t].fix(21.48)
                m.fs.col.vap_in_temperature[t].fix(317.88)
                m.fs.col.bot_pressure[t].fix(107650)
                m.fs.col.vap_in_mole_frac[t, "CO2"].fix(0.11453)
                m.fs.col.vap_in_mole_frac[t, "H2O"].fix(0.08526)
                m.fs.col.vap_in_mole_frac[t, "N2"].fix(0.73821)
                m.fs.col.vap_in_mole_frac[t, "O2"].fix(0.06200)
                # liquid
                m.fs.col.liq_in_flow[t].fix(37.55)
                m.fs.col.liq_in_temperature[t].fix(319.87)
                m.fs.col.liq_in_mole_frac[t, "CO2"].fix(0.00963)
                m.fs.col.liq_in_mole_frac[t, "H2O"].fix(0.87435)
                m.fs.col.liq_in_mole_frac[t, "MEA"].fix(0.11602)
                #rich loading at the bottom of column @ final time
                m.fs.col.loading = Param(initialize=0.4927155969073804)
            #initialize column
            m.fs.col.initialize()
        elif Fpar == 'Stripper':
            m.fs.col.length_col.fix(12.1)
            for t in m.fs.time:
                # vapor
                m.fs.col.vap_in_flow[t].fix(17.496)
                m.fs.col.vap_in_temperature[t].fix(396.6)
                m.fs.col.bot_pressure[t].fix(183430)
                m.fs.col.vap_in_mole_frac[t, "CO2"].fix(0.0145)
                m.fs.col.vap_in_mole_frac[t, "H2O"].fix(0.9855)
                # liquid
                m.fs.col.liq_in_flow[t].fix(84.48)
                m.fs.col.liq_in_temperature[t].fix(382.15)
                m.fs.col.liq_in_mole_frac[t, "CO2"].fix(0.0331)
                m.fs.col.liq_in_mole_frac[t, "H2O"].fix(0.8547)
                m.fs.col.liq_in_mole_frac[t, "MEA"].fix(0.1122)
                #lean loading at the bottom of column @ final time
                m.fs.col.loading = Param(initialize=0.17766107613856313)
            #initialize column
            m.fs.col.initialize(homotopy_steps_h=[0.1, 0.2, 0.4, 0.6, 0.8, 1])
        return m
# ------------------------------------------------------------------------------
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.integration
    def test_steady_state_column_build(self, column_model_ss):
        assert column_model_ss.fs.col.config.dynamic is False
        assert column_model_ss.fs.col.config.liquid_side.transformation_scheme ==\
            'FORWARD'
        assert column_model_ss.fs.col.config.vapor_side.transformation_scheme == \
            'BACKWARD'
        assert degrees_of_freedom(column_model_ss) == 0


    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.integration
    def test_dynamic_column_build(self, column_model_dyn):
        assert column_model_dyn.fs.col.config.dynamic is True
        assert column_model_dyn.fs.col.config.liquid_side.transformation_scheme ==\
            'FORWARD'
        assert column_model_dyn.fs.col.config.vapor_side.transformation_scheme == \
            'BACKWARD'
        assert degrees_of_freedom(column_model_dyn) == 0


    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.integration
    def test_steady_state_column(self, column_model_ss):

        m = column_model_ss
        res = solver.solve(m)

        # Solver status/condition
        assert res.solver.termination_condition == TerminationCondition.optimal

        # Outlet Stream Condition Testing
        assert m.fs.col.vapor_phase.properties[0, 1].temperature.value ==\
            pytest.approx(value(m.fs.col.vapor_exit_temp), abs=1e-4)

        assert m.fs.col.liquid_phase.properties[0, 0].temperature.value ==\
            pytest.approx(value(m.fs.col.liquid_exit_temp), abs=1e-4)

        # CO2 mass balance
        assert value(m.fs.col.vapor_phase.properties[0, 0].flow_mol_comp['CO2'] -
                     m.fs.col.vapor_phase.properties[0, 1].flow_mol_comp['CO2'] +
                     m.fs.col.liquid_phase.properties[0, 1].flow_mol_comp['CO2'] -
                     m.fs.col.liquid_phase.properties[0, 0].flow_mol_comp['CO2']) ==\
            pytest.approx(0, abs=1e-4)


    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.integration
    def test_dynamic_column(self, column_model_dyn):

        m = column_model_dyn
        res = solver.solve(m)

        # Solver status/condition
        assert res.solver.termination_condition == TerminationCondition.optimal

        # Performance Condition Testing at final time
        assert value(m.fs.col.liquid_phase.properties[
                     m.fs.time.last(), 0].mole_frac_comp['CO2'] /
                     m.fs.col.liquid_phase.properties[
                     m.fs.time.last(), 0].mole_frac_comp['MEA']) == \
            pytest.approx(value(m.fs.col.loading), abs=1e-4)

