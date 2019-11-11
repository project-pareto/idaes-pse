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
Tests for tray mixer unit model.

Author: Jaffer Ghouse
"""
import pytest
from pyomo.environ import (ConcreteModel, TerminationCondition,
                           SolverStatus, value)

from idaes.core import (FlowsheetBlock, MaterialBalanceType, EnergyBalanceType,
                        MomentumBalanceType)
from idaes.unit_models.distillation import TrayMixer
from idaes.property_models.activity_coeff_models.BTX_activity_coeff_VLE \
    import BTXParameterBlock
from idaes.core.util.model_statistics import degrees_of_freedom, \
    number_variables, number_total_constraints
from idaes.core.util.testing import get_default_solver


# -----------------------------------------------------------------------------
# Get default solver for testing
solver = get_default_solver()

m = ConcreteModel()
m.fs = FlowsheetBlock(default={"dynamic": False})
m.fs.properties = BTXParameterBlock(default={"valid_phase":
                                             ('Liq', 'Vap'),
                                             "activity_coeff_model":
                                             "Ideal"})

###############################################################################

m.fs.tray_mixer = TrayMixer(default={"property_package": m.fs.properties})

# Set inputs
m.fs.tray_mixer.liq_in_properties[0].flow_mol.fix(1)
m.fs.tray_mixer.liq_in_properties[0].temperature.fix(369)
m.fs.tray_mixer.liq_in_properties[0].pressure.fix(101325)
m.fs.tray_mixer.liq_in_properties[0].mole_frac_comp["benzene"].fix(0.5)
m.fs.tray_mixer.liq_in_properties[0].mole_frac_comp["toluene"].fix(0.5)

m.fs.tray_mixer.vap_in_properties[0].flow_mol.fix(1)
m.fs.tray_mixer.vap_in_properties[0].temperature.fix(370)
m.fs.tray_mixer.vap_in_properties[0].pressure.fix(101325)
m.fs.tray_mixer.vap_in_properties[0].mole_frac_comp["benzene"].fix(0.5)
m.fs.tray_mixer.vap_in_properties[0].mole_frac_comp["toluene"].fix(0.5)

m.fs.tray_mixer.initialize(outlvl=2, solver=solver)

m.fs.tray_mixer.mixed_feed_properties[0].flow_mol.display()
m.fs.tray_mixer.mixed_feed_properties[0].mole_frac_comp.display()
m.fs.tray_mixer.mixed_feed_properties[0].temperature.display()
