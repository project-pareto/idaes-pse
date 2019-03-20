##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes".
##############################################################################
"""
Demonstration and test flowsheet for a dynamic flowsheet.

"""
from __future__ import division
from __future__ import print_function

import matplotlib.pyplot as plt

# Import Pyomo libraries
from pyomo.environ import (ConcreteModel, SolverFactory, TransformationFactory,
                           Var, Constraint)
from pyomo.network import Arc

# Import IDAES core
from idaes.core import FlowsheetBlock

# Import Unit Model Modules
import idaes.property_models.examples.saponification_thermo as thermo_props
import idaes.property_models.examples.saponification_reactions as \
    reaction_props

# Import Unit Model Modules
from idaes.unit_models import CSTR, Mixer


def main():
    """
    Make the flowsheet object, fix some variables, and solve the problem
    """
    # Create a Concrete Model as the top level object
    m = ConcreteModel()

    # Add a flowsheet object to the model
    m.fs = FlowsheetBlock(default={"dynamic": True,
                                   "time_set": [0, 1, 8]})

    # Add property packages to flowsheet library
    m.fs.thermo_params = thermo_props.SaponificationParameterBlock()
    m.fs.reaction_params = reaction_props.SaponificationReactionParameterBlock(
        default={"property_package": m.fs.thermo_params})

    # Create unit models
    m.fs.mix = Mixer(default={"dynamic": False,
                              "property_package": m.fs.thermo_params})
    m.fs.Tank1 = CSTR(default={"property_package": m.fs.thermo_params,
                               "reaction_package": m.fs.reaction_params,
                               "has_holdup": True,
                               "has_equilibrium_reactions": False,
                               "has_heat_transfer": True,
                               "has_pressure_change": False,
                               "dynamic": False})
    m.fs.Tank2 = CSTR(default={"property_package": m.fs.thermo_params,
                               "reaction_package": m.fs.reaction_params,
                               "has_holdup": True,
                               "has_equilibrium_reactions": False,
                               "has_heat_transfer": True,
                               "has_pressure_change": False})

    # Add pressure-flow constraints to Tank 1
    m.fs.Tank1.height = Var(m.fs.time,
                            initialize=1.0,
                            doc="Depth of fluid in tank [m]")
    m.fs.Tank1.area = Var(initialize=1.0,
                          doc="Cross-sectional area of tank [m^2]")
    m.fs.Tank1.flow_coeff = Var(m.fs.time,
                                initialize=5e-5,
                                doc="Tank outlet flow coefficient")

    def geometry(b, t):
        return b.volume[t] == b.area*b.height[t]
    m.fs.Tank1.geometry = Constraint(m.fs.time, rule=geometry)

    def outlet_flowrate(b, t):
        return b.control_volume.properties_out[t].flow_vol == \
                    b.flow_coeff[t]*b.height[t]
    m.fs.Tank1.outlet_flowrate = Constraint(m.fs.time,
                                            rule=outlet_flowrate)

    # Add pressure-flow constraints to tank 2
    m.fs.Tank2.height = Var(m.fs.time,
                            initialize=1.0,
                            doc="Depth of fluid in tank [m]")
    m.fs.Tank2.area = Var(initialize=1.0,
                          doc="Cross-sectional area of tank [m^2]")
    m.fs.Tank2.flow_coeff = Var(m.fs.time,
                                initialize=5e-5,
                                doc="Tank outlet flow coefficient")

    m.fs.Tank2.geometry = Constraint(m.fs.time, rule=geometry)
    m.fs.Tank2.outlet_flowrate = Constraint(m.fs.time,
                                            rule=outlet_flowrate)

    # Make Streams to connect units
    m.fs.stream1 = Arc(source=m.fs.mix.outlet,
                       destination=m.fs.Tank1.inlet)

    m.fs.stream2 = Arc(source=m.fs.Tank1.outlet,
                       destination=m.fs.Tank2.inlet)



    # Discretize time domain
    m.discretizer = TransformationFactory('dae.finite_difference')
    m.discretizer.apply_to(m,
                           nfe=50,
                           wrt=m.fs.time,
                           scheme="BACKWARD")
    
    TransformationFactory("network.expand_arcs").apply_to(m)

    # Set inlet and operating conditions, and some initial conditions.
    m.fs.mix.inlet_1.flow_vol.fix(0.5)
    m.fs.mix.inlet_1.conc_mol_comp[:, "H2O"].fix(55388.0)
    m.fs.mix.inlet_1.conc_mol_comp[:, "NaOH"].fix(100.0)
    m.fs.mix.inlet_1.conc_mol_comp[:, "EthylAcetate"].fix(0.0)
    m.fs.mix.inlet_1.conc_mol_comp[:, "SodiumAcetate"].fix(0.0)
    m.fs.mix.inlet_1.conc_mol_comp[:, "Ethanol"].fix(0.0)
    m.fs.mix.inlet_1.temperature.fix(303.15)
    m.fs.mix.inlet_1.pressure.fix(101325.0)

    m.fs.mix.inlet_2.flow_vol.fix(0.5)
    m.fs.mix.inlet_2.conc_mol_comp[:, "H2O"].fix(55388.0)
    m.fs.mix.inlet_2.conc_mol_comp[:, "NaOH"].fix(0.0)
    m.fs.mix.inlet_2.conc_mol_comp[:, "EthylAcetate"].fix(100.0)
    m.fs.mix.inlet_2.conc_mol_comp[:, "SodiumAcetate"].fix(0.0)
    m.fs.mix.inlet_2.conc_mol_comp[:, "Ethanol"].fix(0.0)
    m.fs.mix.inlet_2.temperature.fix(303.15)
    m.fs.mix.inlet_2.pressure.fix(101325.0)

    m.fs.Tank1.area.fix(1.0)
    m.fs.Tank1.flow_coeff.fix(0.5)
    m.fs.Tank1.heat_duty.fix(0.0)

    m.fs.Tank2.area.fix(1.0)
    m.fs.Tank2.flow_coeff.fix(0.5)
    m.fs.Tank2.heat_duty.fix(0.0)

    # Set initial conditions
    m.fs.fix_initial_conditions()

    # Initialize Units
    m.fs.mix.initialize()

    m.fs.Tank1.initialize(state_args={
            "flow_vol": 1.0,
            "conc_mol_comp": {"H2O": 55388.0,
                              "NaOH": 100.0,
                              "EthylAcetate": 100.0,
                              "SodiumAcetate": 0.0,
                              "Ethanol": 0.0},
            "temperature": 303.15,
            "pressure": 101325.0})

    m.fs.Tank2.initialize(state_args={
            "flow_vol": 1.0,
            "conc_mol_comp": {"H2O": 55388.0,
                              "NaOH": 100.0,
                              "EthylAcetate": 100.0,
                              "SodiumAcetate": 0.0,
                              "Ethanol": 0.0},
            "temperature": 303.15,
            "pressure": 101325.0})

    # Create a solver
    solver = SolverFactory('ipopt')
    results = solver.solve(m.fs)

    # Make a step disturbance in feed and solve again
    for t in m.fs.time:
        if t > 1.0:
            m.fs.mix.inlet_2.conc_mol_comp[t, "EthylAcetate"].fix(90.0)
    results = solver.solve(m.fs)

    # Print results
    print(results)

    # For testing purposes
    return(m, results)


def plot_results(m):
    time = []
    a1 = []
    b1 = []
    c1 = []
    d1 = []
    a2 = []
    b2 = []
    c2 = []
    d2 = []

    for t in m.fs.time:
        time.append(t)
        a1.append(m.fs.Tank1.outlet.conc_mol_comp[t, "NaOH"].value)
        b1.append(m.fs.Tank1.outlet.conc_mol_comp[t, "EthylAcetate"].value)
        c1.append(m.fs.Tank1.outlet.conc_mol_comp[t, "SodiumAcetate"].value)
        d1.append(m.fs.Tank1.outlet.conc_mol_comp[t, "Ethanol"].value)
        a2.append(m.fs.Tank2.outlet.conc_mol_comp[t, "NaOH"].value)
        b2.append(m.fs.Tank2.outlet.conc_mol_comp[t, "EthylAcetate"].value)
        c2.append(m.fs.Tank2.outlet.conc_mol_comp[t, "SodiumAcetate"].value)
        d2.append(m.fs.Tank2.outlet.conc_mol_comp[t, "Ethanol"].value)

    plt.figure("Tank 1 Outlet")
    plt.plot(time, a1, label='NaOH')
    plt.plot(time, b1, label='EthylAcetate')
    plt.plot(time, c1, label='SodiumAcetate')
    plt.plot(time, d1, label='Ethanol')
    plt.legend()
    plt.grid()
    plt.xlabel("Time [s]")
    plt.ylabel("Concentration [mol/m^3]")

    plt.figure("Tank 2 Outlet")
    plt.plot(time, a2, label='NaOH')
    plt.plot(time, b2, label='EthylAcetate')
    plt.plot(time, c2, label='SodiumAcetate')
    plt.plot(time, d2, label='Ethanol')
    plt.legend()
    plt.grid()
    plt.xlabel("Time [s]")
    plt.ylabel("Concentration [mol/m^3]")
    plt.show(block=True)


if __name__ == "__main__":
    m, results = main()
    plot_results(m)
