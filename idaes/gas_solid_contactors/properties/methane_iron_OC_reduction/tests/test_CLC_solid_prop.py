###############################################################################
# Copyright
# =========
#
# Institute for the Design of Advanced Energy Systems Process Systems Engineering
# Framework (IDAES PSE Framework) was produced under the DOE Institute for the
# Design of Advanced Energy Systems (IDAES), and is copyright (c) 2018-2021 by the
# software owners: The Regents of the University of California, through Lawrence
# Berkeley National Laboratory,  National Technology & Engineering Solutions of
# Sandia, LLC, Carnegie Mellon University, West Virginia University Research
# Corporation, et al.  All rights reserved.
#
# NOTICE.  This Software was developed under funding from the U.S. Department of
# Energy and the U.S. Government consequently retains certain rights. As such, the
# U.S. Government has been granted for itself and others acting on its behalf a
# paid-up, nonexclusive, irrevocable, worldwide license in the Software to
# reproduce, distribute copies to the public, prepare derivative works, and
# perform publicly and display publicly, and to permit other to do so. Copyright
# (C) 2018-2019 IDAES - All Rights Reserved
#
###############################################################################
"""
Tests for CLC solid phase thermo state block; tests for construction and solve
Author: Chinedu Okoli
"""

import pytest

from pyomo.environ import (ConcreteModel,
                           TerminationCondition,
                           SolverStatus,
                           Var)

from idaes.core import FlowsheetBlock

from idaes.core.util.model_statistics import degrees_of_freedom

from idaes.core.util.testing import initialization_tester
from idaes.core.util import get_solver

from idaes.gas_solid_contactors.properties.methane_iron_OC_reduction. \
    solid_phase_thermo import SolidPhaseParameterBlock

# Get default solver for testing
solver = get_solver()


# -----------------------------------------------------------------------------
@pytest.fixture(scope="class")
def solid_prop():
    m = ConcreteModel()
    m.fs = FlowsheetBlock(default={"dynamic": False})

    # solid properties and state inlet block
    m.fs.properties = SolidPhaseParameterBlock()

    m.fs.unit = m.fs.properties.build_state_block(
        default={"parameters": m.fs.properties,
                 "defined_state": True})

    m.fs.unit.flow_mass.fix(1)
    m.fs.unit.particle_porosity.fix(0.27)
    m.fs.unit.temperature.fix(1183.15)
    m.fs.unit.mass_frac_comp["Fe2O3"].fix(0.45)
    m.fs.unit.mass_frac_comp["Fe3O4"].fix(1e-9)
    m.fs.unit.mass_frac_comp["Al2O3"].fix(0.55)

    return m


@pytest.mark.unit
def test_build_inlet_state_block(solid_prop):
    assert isinstance(solid_prop.fs.unit.dens_mass_skeletal, Var)
    assert isinstance(solid_prop.fs.unit.enth_mol_comp, Var)
    assert isinstance(solid_prop.fs.unit.enth_mass, Var)
    assert isinstance(solid_prop.fs.unit.cp_mol_comp, Var)
    assert isinstance(solid_prop.fs.unit.cp_mass, Var)


@pytest.mark.unit
def test_setInputs_state_block(solid_prop):
    assert degrees_of_freedom(solid_prop.fs.unit) == 0


@pytest.mark.solver
@pytest.mark.skipif(solver is None, reason="Solver not available")
@pytest.mark.component
def test_initialize(solid_prop):
    initialization_tester(
            solid_prop)

@pytest.mark.solver
@pytest.mark.skipif(solver is None, reason="Solver not available")
@pytest.mark.component
def test_solve(solid_prop):

    assert hasattr(solid_prop.fs.unit, "dens_mass_skeletal")
    assert hasattr(solid_prop.fs.unit, "cp_mass")
    assert hasattr(solid_prop.fs.unit, "enth_mass")

    results = solver.solve(solid_prop)

    # Check for optimal solution
    assert results.solver.termination_condition == \
        TerminationCondition.optimal
    assert results.solver.status == SolverStatus.ok


@pytest.mark.solver
@pytest.mark.skipif(solver is None, reason="Solver not available")
@pytest.mark.component
def test_solution(solid_prop):
    assert (pytest.approx(3251.75, abs=1e-2) ==
            solid_prop.fs.unit.dens_mass_skeletal.value)
    assert (pytest.approx(1, abs=1e-2) ==
            solid_prop.fs.unit.cp_mass.value)
    assert (pytest.approx(0.0039, abs=1e-2) ==
            solid_prop.fs.unit.enth_mass.value)
