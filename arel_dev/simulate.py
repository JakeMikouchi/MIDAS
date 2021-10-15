import os
import sys
import copy
import math
import numpy
import pickle
import random
from solution_types import Solution

class Simulate_Assembly_Solution(Solution):
    """
    Class for optimizing the lattice layers of an assembly in Simulate.

    Parameters: None

    Written by Brian Andersen 1/8/2020
    """
    def __init__(self):
        Solution.__init__(self)
        self.type        = None
        self.number_pins = None
        self.model       = None

    def add_additional_information(self,settings):
        """
        Adds information on assembly type, the number of pins in the assembly,
        and the model type to the class instance.

        Parameters:
            settings: dict
                The additional settings added to the optimization.

        Written by Brian Andersen 1/8/2020
        """
        info = settings['genome']['assembly_data']
        if 'type' in info:
            self.type = info['type']
        if 'pins' in info:
            self.number_pins = info['pins']
        if 'model' in info:
            self.model = info['model']
        if 'fixed_problem' in settings['optimization']:
            self.fixed_genome = settings['optimization']['fixed_problem']

    def evaluate(self):
        """
        Evaluates the class instance.

        Parameters: None

        Written by Brian Andersen 1/8/2020
        """
        os.system("mkdir {}".format(self.name))
        File_Writer.cms_link_file(self.genome,self.name)
        if self.type.lower() == 'bwr':
            File_Writer.bwr_assembly(self.genome,self.name)
        else:
            File_Writer.pwr_assembly(self.genome,self.name)

        cms_command = "/cm/shared/apps/ncsu/CasmoSimulate/bin/cmslink"
        sim_command = "/cm/shared/apps/ncsu/CasmoSimulate/bin/simulate3"
        os_command = "cd {}; ".format(self.name)
        os_command +=  "{} {}_cms.inp; ".format(cms_command,self.name)
        os_command += "{} {}_sim.inp".format(sim_command,self.name)
        os.system(os_command)

        file_ = open("{}/{}_sim.out".format(self.name,self.name),'r')
        file_lines = file_.readlines()
        file_.close()

        power_dictionary = None
        kinf_list = None

        if 'BTF' in self.parameters:
            if not power_dictionary:
                power_dictionary = Extractor.powers3D(file_lines,self.number_pins)
            btf_list,max_btf = Calculator.calculate_BTF(power_dictionary,self.model)
            self.parameters['BTF']['value'] = float(max_btf)
        if '2D_BTF' in self.parameters:
            if not power_dictionary:
                power_dictionary = Extractor.powers2D(file_lines,self.number_pins)
            btf_list,max_btf = Calculator.calculate_BTF(power_dictionary,self.model)
            self.parameters['2D_BTF']['value'] = float(max_btf)
        if 'max_kinf' in self.parameters:
            if not kinf_list:
                kinf_list = Extractor.keff_list(file_lines,self.type)
            self.parameters['max_kinf']['value'] = max(kinf_list)
        if 'eoc_kinf' in self.parameters:
            if not kinf_list:
                kinf_list = Extractor.keff_list(file_lines,self.type)
            self.parameters['eoc_kinf']['value'] = kinf_list[-1]

class Simulate_Loading_Pattern_Solution(Solution):
    """
    Solution class for designing loading patterns in Simulate.

    Parameters: None

    Written by Brian Andersen. 1/8/2020
    """
    def __init__(self):
        Solution.__init__(self)
        self.type        = None
        self.number_pins = None
        self.model       = None
        self.symmetry    = None
        self.core_width  = 15
        self.axial_nodes = 25
        self.batch_number = 0
        self.core_edits = None
        self.load_point = 0.
        self.depletion = 20.
        
        self.location_map = [  "H-08", "G-08", "F-08", "E-08", "D-08", "C-08", "B-08", "A-08",
                               "H-09", "G-09", "F-09", "E-09", "D-09", "C-09", "B-09", "A-09",
                               "H-10", "G-10", "F-10", "E-10", "D-10", "C-10", "B-10",
                               "H-11", "G-11", "F-11", "E-11", "D-11", "C-11", "B-11",
                               "H-12", "G-12", "F-12", "E-12", "D-12", "C-12",
                               "H-13", "G-13", "F-13", "E-13", "D-13",
                               "H-14", "G-14", "F-14", "E-14",
                               "H-15", "G-15"]
        self.position_map = [[0,0],  [0,1],  [0,2],  [0,3],  [0,4],  [0,5],  [0,6],  [0,7],
                             [1,0],  [1,1],  [1,2],  [1,3],  [1,4],  [1,5],  [1,6],  [1,7],
                             [2,0],  [2,1],  [2,2],  [2,3],  [2,4],  [2,5],  [2,6],
                             [3,0],  [3,1],  [3,2],  [3,3],  [3,4],  [3,5],  [3,6],
                             [4,0],  [4,1],  [4,2],  [4,3],  [4,4],  [4,5],
                             [5,0],  [5,1],  [5,2],  [5,3],  [5,4], 
                             [6,0],  [6,1],  [6,2],  [6,3],  
                             [7,0],  [7,1]]

    def add_additional_information(self,settings):
        """
        Adds information on assembly type, the number of pins in the assembly,
        and the model type to the class instance.

        Parameters
            settings: The settings dictionary for the parameters.

        WRitten by Brian Andersen. 1/9/2020
        """
        info = settings['genome']['assembly_data']
        if 'type' in info:
            self.type = info['type']
        if 'pins' in info:
            self.number_pins = info['pins']
        if 'boron' in info:
            self.boron = info['boron']
        if 'model' in info:
            self.model = info['model']
        if 'core_width' in info:
            self.core_width = info['core_width']
        if 'symmetry' in info:
            self.symmetry = info['symmetry']
        if 'depletion_arguments' in info:
            self.depletion_arguments = info['depletion_arguments']
        if 'axial_nodes' in info:
            self.axial_nodes = info['axial_nodes']
        if 'batch_number' in info:
            self.batch_number = info['batch_number']
        if 'depletion' in info:
            self.depletion = info['depletion']
        if 'cs_library' in info:
            self.library = info['cs_library']
        if 'restart_file' in info:
            self.restart_file = info['restart_file']
        if 'BURNED_ASSEMBLY' in settings['genome']['chromosomes']: 
            foo = settings['genome']['chromosomes']['BURNED_ASSEMBLY']
            self.center_burned_assembly = foo['center_assembly']
        if 'state_list' in info:
            self.state_list = info['state_list']
        if 'load_point' in info:
            self.load_point = info['load_point']
        if 'power' in info:
            self.power = info['power']
        if 'flow' in info:
            self.flow = info['flow']
        if 'pressure' in info:
            self.pressure = info['pressure']
        if 'inlet_temperature' in info:
            self.inlet_temperature = info['inlet_temperature']
        if 'fixed_problem' in settings['optimization']:
            self.fixed_genome = settings['optimization']['fixed_problem']
        if 'map_size' in info:
            self.map_size= info['map_size']
        if 'reflector' in info:
            self.reflector_present = info['reflector']
        if 'number_assemblies' in info:
            self.number_assemblies = info['number_assemblies']
        if 'core_edits' in info:
            self.core_edits = info['core_edits']
        if 'fuel_segments' in info:
            self.fuel_segments = info['fuel_segments']
        else:
            if self.batch_number >= 2:
                print("WARNING: No fuel segments provided to simulate. Simulate run may fail.")
 
    def generate_initial(self,chromosome_map):
        """
        Generates the initial solutions to the optimization problem.

        Parameters: 
            chromosome_map: Dictionary
                The genome portion of the dictionary settings file. 

        Written by Brian Andersen. 1/9/2020
        """
        chromosome_length = None
        chromosome_list = list(chromosome_map.keys())
        if 'symmetry_list' in chromosome_list:
            chromosome_list.remove('symmetry_list')

        for chromosome in chromosome_list:
            if chromosome_length is None:
                chromosome_length = len(chromosome_map[chromosome]['map'])
            elif len(chromosome_map[chromosome]['map']) == chromosome_length:
                pass
            else:
                raise ValueError("Chromosome Maps are of unequal length")

        self.genome = []                                #Unburnt assemblies
        for i in range(chromosome_length):              #better off just being implemented
            no_gene_found = True                        #as a single gene.
            while no_gene_found:
                gene = random.choice(chromosome_list)
                if chromosome_map[gene]['map'][i]:
                    self.genome.append(gene)
                    no_gene_found = False

    def generate_initial_fixed(self,chromosome_map,gene_groups):
        """
        Generates initial solution when only specific number of assemblies
        may be used.

        Written by Brian Andersen 3/15/2020
        """
        chromosome_length = None
        chromosome_list = list(chromosome_map.keys())
        if 'symmetry_list' in chromosome_list:
            chromosome_list.remove('symmetry_list')

        for chromosome in chromosome_list:
            if chromosome_length is None:
                chromosome_length = len(chromosome_map[chromosome]['map'])
            elif len(chromosome_map[chromosome]['map']) == chromosome_length:
                pass
            else:
                raise ValueError("Chromosome Maps are of unequal length")

        no_valid_solution = True
        while no_valid_solution:
            no_valid_solution = False
            my_group = copy.deepcopy(gene_groups)
            self.genome = [None]*chromosome_length
            for i in range(chromosome_length):
                no_gene_found = True
                attempt_counter = 0
                while no_gene_found:
                    gene = random.choice(chromosome_list)
                    if 'unique' in chromosome_map[gene]:
                        if chromosome_map[gene]['unique']:
                            if gene in self.genome:
                                pass
                            else:
                                #This else loop activates if the gene is labeled unique but is not used. 
                                if chromosome_map[gene]['map'][i] == 1:
                                    if i in chromosome_map['symmetry_list']:
                                        if my_group[chromosome_map[gene]['gene_group']] > 1:
                                            self.genome[i] = gene
                                            no_gene_found = False
                                            my_group[chromosome_map[gene]['gene_group']] -= 2
                                    else:
                                        if my_group[chromosome_map[gene]['gene_group']] > 0:
                                            self.genome[i] = gene
                                            no_gene_found = False
                                            my_group[chromosome_map[gene]['gene_group']] -= 1            
                        else:
                            #adding unique loop above this code
                            if chromosome_map[gene]['map'][i] == 1:
                                if i in chromosome_map['symmetry_list']:
                                    if my_group[chromosome_map[gene]['gene_group']] > 1:
                                        self.genome[i] = gene
                                        no_gene_found = False
                                        my_group[chromosome_map[gene]['gene_group']] -= 2
                                else:
                                    if my_group[chromosome_map[gene]['gene_group']] > 0:
                                        self.genome[i] = gene
                                        no_gene_found = False
                                        my_group[chromosome_map[gene]['gene_group']] -= 1
                    else:
                        #adding unique loop above this code
                        if chromosome_map[gene]['map'][i] == 1:
                            if i in chromosome_map['symmetry_list']:
                                if my_group[chromosome_map[gene]['gene_group']] > 1:
                                    self.genome[i] = gene
                                    no_gene_found = False
                                    my_group[chromosome_map[gene]['gene_group']] -= 2
                            else:
                                if my_group[chromosome_map[gene]['gene_group']] > 0:
                                    self.genome[i] = gene
                                    no_gene_found = False
                                    my_group[chromosome_map[gene]['gene_group']] -= 1
                    attempt_counter += 1
                    if attempt_counter == 100:
                        no_gene_found = False
                        no_valid_solution = True

    def evaluate(self):
        """
        Evaluates Simulate Loading Pattern Solutions to core optimization

        Parameters: None

        Written by Brian Andersen. 1/8/2020
        """
        File_Writer.write_input_file(self)
        sim_command = "~/../../../cm/shared/apps/ncsu/CasmoSimulate/bin/simulate3"
        line_ = "cd {} ; ".format(self.name)
        line_ += "{} {}_sim.inp".format(sim_command,self.name)
        os.system(line_)

        file_ = open("{}/{}_sim.out".format(self.name,self.name))
        file_lines = file_.readlines()
        file_.close()

        if 'eoc_keff' in self.parameters:
            keff_list = Extractor.core_keff_list(file_lines)
            self.parameters['eoc_keff']['value'] = keff_list[-1]
        if "eoc_boron" in self.parameters:
            boron_list = Extractor.boron_list(file_lines)
            self.parameters["eoc_boron"]['value'] = boron_list[-1]
        if "cycle_length" in self.parameters:
            EFPD_list = Extractor.efpd_list(file_lines)
            self.parameters['cycle_length']['value'] = EFPD_list[-1]
        if "FDeltaH" in self.parameters:
            FDH_list = Extractor.FDH_list(file_lines)
            self.parameters['FDeltaH']['value'] = max(FDH_list)
        if "PinPowerPeaking" in self.parameters:
            peak_list = Extractor.pin_peaking_list(file_lines)
            self.parameters['PinPowerPeaking']['value'] = max(peak_list)
        if 'exposure' in self.parameters:
            exposure_list = Extractor.burnup_list(file_lines)
            self.parameters['exposure']['value'] = exposure_list[-1]
        if "max_boron" in self.parameters:
            boron_list = Extractor.boron_list(file_lines)
            self.parameters["max_boron"]['value'] = max(boron_list)
        if 'assembly_power' in self.parameters:
            radial_peaking = Extractor.assembly_peaking_factors(file_lines)
            max_peaking = 0.0
            for depl in radial_peaking:
                for row in radial_peaking[depl]:
                    for col in radial_peaking[depl][row]:
                        if radial_peaking[depl][row][col] > max_peaking:
                            max_peaking = radial_peaking[depl][row][col]
            self.parameters['assembly_power']['value'] = max_peaking
        
        if 'old_assemblies' in self.parameters:
            burned_assem_list = []
            burn_count = 0
            for gene in self.genome['loading_pattern']:
                if gene == 'BURNED_ASSEMBLY':
                    assy = self.genome['BURNED_ASSEMBLY'][burn_count]
                    burned_assem_list.append(assy)
                    burn_count += 1

            self.parameters["old_assemblies"]['value'] = burn_count*4

class Unique_Assembly_Loading_Pattern_Solution(Simulate_Loading_Pattern_Solution):
    """
    Solution class used for optimizing the loading pattern of a pwr core
    using a fixed set of genomes.

    Parameters: None

    Written by Brian Andersen. 1/8/2020
    """
    def __init__(self):
        Simulate_Loading_Pattern_Solution.__init__(self)

    def generate_initial(self,chromosome_map):
        """
        Generates an initial solution to the optimization problem using
        all genes in the fixed genome problem.

        Parameters: None

        Written by Brian Andersen. 1/8/2020
        """
        chromosome_list = list(chromosome_map.keys())
        self.genome = random.sample(chromosome_list,len(chromosome_list))
        bad_gene_list = []
        for i,gene in enumerate(self.genome):
            if chromosome_map[gene]['map'][i] == 1:
                pass
            else:
                bad_gene_list.append(gene)

        for i,gene in enumerate(self.genome):
            if chromosome_map[gene]['map'][i] == 1:
                pass
            else:
                for ge in bad_gene_list:
                    if chromosome_map[ge]['map'][i] == 1:
                        self.genome[i] = ge
                        bad_gene_list.remove(ge)

    def evaluate(self):
        """
        Evaluates the Simulate Loading Pattern Solutions to the 
        core optimization.

        Parameters: None

        Written by Brian Andersen. 1/8/2020
        """
        File_Writer.write_fixed_gene_reload_core(self)
        sim_command = "~/../../../cm/shared/apps/ncsu/CasmoSimulate/bin/simulate3"
        line_ = "cd {} ; ".format(self.name)
        line_ += "{} {}_sim.inp".format(sim_command,self.name)
        os.system(line_)

        file_ = open("{}/{}_sim.out".format(self.name,self.name))
        file_lines = file_.readlines()
        file_.close()

        if 'eoc_keff' in self.parameters:
            keff_list = Extractor.core_keff_list(file_lines)
            self.parameters['eoc_keff']['value'] = keff_list[-1]
        if "eoc_boron" in self.parameters:
            boron_list = Extractor.boron_list(file_lines)
            self.parameters["eoc_boron"]['value'] = boron_list[-1]
        if "cycle_length" in self.parameters:
            EFPD_list = Extractor.efpd_list(file_lines)
            self.parameters['cycle_length']['value'] = EFPD_list[-1]
        if "FDeltaH" in self.parameters:
            FDH_list = Extractor.FDH_list(file_lines)
            self.parameters['FDeltaH']['value'] = max(FDH_list)
        if "PinPowerPeaking" in self.parameters:
            peak_list = Extractor.pin_peaking_list(file_lines)
            self.parameters['PinPowerPeaking']['value'] = max(peak_list)
        if "max_boron" in self.parameters:
            boron_list = Extractor.boron_list(file_lines)
            self.parameters["max_boron"]['value'] = max(boron_list)
        if 'assembly_power' in self.parameters:
            radial_peaking = Extractor.assembly_peaking_factors(file_lines)
            max_peaking = 0.0
            for depl in radial_peaking:
                for row in radial_peaking[depl]:
                    for col in radial_peaking[depl][row]:
                        if radial_peaking[depl][row][col] > max_peaking:
                            max_peaking = radial_peaking[depl][row][col]
            self.parameters['assembly_power']['value'] = max_peaking
        if 'old_assemblies' in self.parameters:
            burned_assem_list = []
            burn_count = 0
            for gene in self.genome['loading_pattern']:
                if gene == 'BURNED_ASSEMBLY':
                    assy = self.genome['BURNED_ASSEMBLY'][burn_count]
                    burned_assem_list.append(assy)
                    burn_count += 1

            self.parameters["old_assemblies"]['value'] = burn_count*4

class Extractor(object):
    """
    Class for organizing the functions used to read the output files produced
    by Simulate.

    Written by Brian Andersen. 1/8/2020
    """
    @staticmethod
    def core_keff_list(file_lines):
        """
        Extracts the core K-effective value from the provided simulate file lines.

        Written by Brian Andersen. 3/13/2020
        """
        keff_list = []
        for line in file_lines:
            if "K-effective . . . . . . . . . . . . ." in line:
                elems = line.strip().split()
                keff_list.append(float(elems[-1]))

        if not keff_list:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return keff_list
    
    @staticmethod
    def powers3D(file_lines,number_pins):
        """
        Extracts the pin powers from the output solution file as a dictionary
        with the assembly labels as the dictionary keys. 
 
        Parameters
        --------------
        file_lines: List
            The lines of the Simulate output file being analyzed.
        tag: STR
            The tag being used to define the assembly.

        Written by Brian Andersen. 1/9/2020
        """
        assembly_dictionary = {}
        boundary_list = []
        nodal_boundary_search_elems = ['Plane','Nodal','Boundaries:']
        assigning_axial_heights = False
        
        searching_for_powers = False
        for line in file_lines:
            elems = line.strip().split()
            if not elems:
                pass
            else:
                if elems == nodal_boundary_search_elems:
                    assigning_axial_heights = True
                if assigning_axial_heights:
                    if elems[0] == '*******************************************':
                        if elems[1] == '0.000':
                            assigning_axial_heights = False
                        else:
                            boundary_list.insert(0,elems[1])
                if 'Assembly Label:' in line:
                    line = line.replace(","," ")
                    elems = line.strip().split()
                    current_label = elems[3]
                    current_height = boundary_list[int(elems[13])-1]
                    if current_label in assembly_dictionary:
                        pass
                    else:
                        assembly_dictionary[current_label] = {}
                    if current_burnup in assembly_dictionary[current_label]:
                        pass
                    else:
                        assembly_dictionary[current_label][current_burnup] = {}
                        for height in boundary_list:
                            assembly_dictionary[current_label][current_burnup][height] = {}
                            for i in range(number_pins):
                                assembly_dictionary[current_label][current_burnup][height][i] = None
                if 'Case  1 Step' in line:
                    current_burnup = float(elems[-2])
                if "'3PXP' - Pin Power  Distribution:" in line:
                    searching_for_powers = True
                    pin_count = 0
                if searching_for_powers:
                    line = line.replace(":"," ")
                    elems = line.strip().split()
                    if len(elems) > 1:
                        if elems[0] == "'3PXP'":
                            pass
                        else:
                            for el in elems:
                                assembly_dictionary[current_label][current_burnup][current_height][pin_count] = float(el)
                                pin_count += 1
                            if pin_count == number_pins:
                                searching_for_powers = False
        if not assembly_dictionary:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return assembly_dictionary

    @staticmethod
    def powers2D(file_lines,number_pins):
        """
        Extracts the radial power matrix from the simulate output file as
        a dictionary with the assembly label and depletion as the keys.

        Parameters
            file_lines: list
                All the output lines of the simulate file as a list.
            number_pins: int
                The number of fuel rods in each assembly.
        
        Written by Brian Andersen. 1/9/2020
        """
        assembly_dictionary = {}
        boundary_list = []
        nodal_boundary_search_elems = ['Plane','Nodal','Boundaries:']
        assigning_axial_heights = False
        
        searching_for_powers = False
        for line in file_lines:
            elems = line.strip().split()
            if not elems:
                pass
            else:
                if elems == nodal_boundary_search_elems:
                    assigning_axial_heights = True
                if assigning_axial_heights:
                    if elems[0] == '*******************************************':
                        if elems[1] == '0.000':
                            assigning_axial_heights = False
                        else:
                            boundary_list.insert(0,elems[1])
                if 'Assembly Label:' in line:
                    line = line.replace(","," ")
                    elems = line.strip().split()
                    current_label = elems[3]
                    current_height = boundary_list[int(elems[13])-1]
                    if current_label in assembly_dictionary:
                        pass
                    else:
                        assembly_dictionary[current_label] = {}
                    if current_burnup in assembly_dictionary[current_label]:
                        pass
                    else:
                        assembly_dictionary[current_label][current_burnup] = {}
                        for height in boundary_list:
                            assembly_dictionary[current_label][current_burnup][height] = {}
                            for i in range(number_pins):
                                assembly_dictionary[current_label][current_burnup][height][i] = None
                if 'Case  1 Step' in line:
                    current_burnup = float(elems[-2])
                if "'2PXP' - Planar Pin Powers" in line:
                    searching_for_powers = True
                    pin_count = 0
                if searching_for_powers:
                    line = line.replace(":"," ")
                    elems = line.strip().split()
                    if len(elems) > 1:
                        if elems[0] == "'2PXP'":
                            pass
                        else:
                            for el in elems:
                                assembly_dictionary[current_label][current_burnup][current_height][pin_count] = float(el)
                                pin_count += 1
                            if pin_count == number_pins:
                                searching_for_powers = False

        if not assembly_dictionary:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return assembly_dictionary

    @staticmethod
    def assembly_peaking_factors(file_lines):
        """
        Extracts the assembly radial power peaking factors as a dictionary
        with the depletion step in GWD/MTU as the dictionary keys.

        Parameters
            file_lines: list
                All the output lines of the simulate file as a list.

        Written by Brian Andersen. 1/9/2020
        """
        radial_power_dictionary = {}
        searching_ = False
        for line in file_lines:
            if "Case" in line and "GWd/MT" in line:
                elems = line.strip().split()
                depl = elems[-2]
                if depl in radial_power_dictionary:
                    pass
                else:
                    radial_power_dictionary[depl] = {}
            if "**   H-     G-     F-     E-     D-     C-     B-     A-     **" in line:
                searching_ = False
                
            if searching_:
                elems = line.strip().split()
                if elems[0] == "**":
                    pos_list = elems[1:-1]
                else:
                    radial_power_dictionary[depl][elems[0]] = {}
                    for i,el in enumerate(elems[1:-1]):
                        radial_power_dictionary[depl][elems[0]][pos_list[i]] = float(el)
                        
            if "PRI.STA 2RPF  - Assembly 2D Ave RPF - Relative Power Fraction" in line:
                searching_ = True
        
        if not radial_power_dictionary:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return radial_power_dictionary

    @staticmethod
    def linear_power_rate(key_list,file_lines):
        """
        Extracts the linear power rate from Simulate as a dictionary.

        Parameters
            key_list: List of the assemblies in the reactor core, used as 
                keys for the linear power rate dictionary.
            file_lines: list
                All the output lines of the simulate file as a list.

        Written by Brian Andersen. 1/9/2020
        """
        linear_power_dictionary = {}
        for key in key_list:
            linear_power_dictionary[key] = {}

        searching_powers = False
        for line in file_lines:
            if "Case" in line and "GWd/MT" in line:
                elems = line.strip().split()
                depl = elems[-2]

            if "**   H-     G-     F-     E-     D-     C-     B-     A-     **" in line:
                searching_powers = False

            if searching_powers:
                elems = line.strip().split()
                if elems[0] == "Renorm":
                    pass
                elif elems[0] == "**":
                    pass
                else:
                    for el in elems[1:-1]:
                        key = key_list[assembly_count]
                        linear_power_dictionary[key][depl] = float(el) 
                        assembly_count += 1
            
            if "PIN.EDT 2KWF  - Peak Pin Power: (kW/ft)      Assembly 2D" in line:
                searching_powers = True
                assembly_count = 0
                for key in key_list:
                    linear_power_dictionary[key][depl] = None

        if not linear_power_dictionary:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return linear_power_dictionary

    @staticmethod
    def efpd_list(file_lines):
        """
        Returns a list of EFPD values for each cycle exposure in the simulate
        file.

        Parameters:
        file_lines: list
            All the output lines of the simulate file as a list.

        Written by Brian Andersen 12/7/2019
        """
        list_ = []
        for line in file_lines:
            if "Cycle Exp." in line:
                if "EFPD" in line:
                    elems = line.strip().split()
                    spot = elems.index('EFPD')
                    list_.append(float(elems[spot-1]))

        if not list_:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return list_

    @staticmethod
    def FDH_list(file_lines):
        """
        Returns a list of F-delta-H values for each cycle exposure in the simulate
        file.

        Parameters:
        file_lines: list
            All the output lines of the simulate file as a list.

        Written by Brian Andersen 12/7/2019
        """
        list_ = []
        for line in file_lines:
            if "F-delta-H" in line:
                elems = line.strip().split()
                spot = elems.index('F-delta-H')
                list_.append(float(elems[spot+1]))
        
        if not list_:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return list_

    @staticmethod
    def pin_peaking_list(file_lines):
        """
        Returns a list of pin peaking values, Fq, for each cycle exposure in the simulate
        file.

        Parameters:
        file_lines: list
            All the output lines of the simulate file as a list.

        Written by Brian Andersen 12/7/2019
        """
        list_ = []
        for line in file_lines:
            if "Max-3PIN" in line:
                elems = line.strip().split()
                spot = elems.index('Max-3PIN')
                list_.append(float(elems[spot+1]))
        
        if not list_:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return list_

    @staticmethod
    def radial_power_dictionary(file_lines):
        """
        Extracts the radial power matrix from the simulate output file and 
        returns them as a dictionary.

        Parameters:
        file_lines: list
            All the output lines of the simulate file as a list.

        Written by Brian Andersen 12/7/2019
        """
        power_dictionary = {}
        searching_pin_powers = False
        for line in file_lines:
            if "Assembly Label:" in line and "Serial =" in line:
                new_line = line.replace(","," ")
                elems = new_line.strip().split()
                assembly_label = elems[3]
                serial_number = elems[6]
                planar = elems[13]
                key_tuple = (assembly_label,serial_number)
                if key_tuple in power_dictionary:
                    pass
                else:
                    power_dictionary[key_tuple] = {}
        
            if "Case" in line and "GWd/MT" in line:
                elems = line.strip().split()
                depletion = elems[-2]

            if searching_pin_powers:
                if 'PIN.EDT 3PIN  - Peak Pin Power:              Assembly 3D' in line:
                    searching_pin_powers = False
                    if depletion in power_dictionary[key_tuple]:
                        pass
                    else:
                        power_dictionary[key_tuple][depletion] = {}
                    power_dictionary[key_tuple][depletion][planar] = pin_power_matrix
                elif '1S I M U L A T E - 3 **' in line:
                    searching_pin_powers = False
                    if depletion in power_dictionary[key_tuple]:
                        pass
                    else:
                        power_dictionary[key_tuple][depletion] = {}
                    power_dictionary[key_tuple][depletion][planar] = pin_power_matrix
                else:
                    column_count = 0
                    new_line = line.replace(":","")
                    new_line = new_line.replace("-","")
                    new_line = new_line.replace("+","")
                    elems = new_line.strip().split()
                    if not elems:
                        pass
                    else:
                        for power in elems:
                            pin_power_matrix[row_count,column_count] = float(power)
                            column_count += 1
                        row_count += 1

            if "'3PXP' - Pin Power  Distribution:" in line:
                searching_pin_powers = True
                pin_power_matrix = numpy.zeros([17,17])
                row_count = 0

        if not power_dictionary:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return power_dictionary

    @staticmethod
    def boron_list(file_lines):
        """
        Returns a list of boron values in PPM at each depletion step.

        Parameters:
        file_lines: list
            All the output lines of the simulate file as a list.

        Written by Brian Andersen 12/7/2019
        """
        boron_list = []
        for line in file_lines:
            if "Boron" in line and "(ppm)" in line:
                elems = line.strip().split()
                boron_list.append(float(elems[-1]))

        if not boron_list:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return boron_list

    @staticmethod
    def keff_list(file_lines,assembly_type):
        """
        Returns a list of kinf values from Simulate3.
        """
        kinf_list = []
        searching_for_kinf = False
        for line in file_lines:
            elems = line.strip().split()
            if not elems:
                pass
            else:
                if assembly_type.upper() == 'BWR':
                    if searching_for_kinf:
                        if elems[0] == '1':
                            kinf_list.append(float(elems[1]))
                            searching_for_kinf = False
                    if "PRI.STA 2KIN  - Assembly 2D Ave KINF - K-infinity" in line:
                        searching_for_kinf = True
        
        if not kinf_list:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return kinf_list

    @staticmethod
    def relative_power(file_lines):
        """
        Extracts the Relative Core Power from the provided simulate file lines.

        Written by Brian Andersen. 3/13/2020
        """
        relative_powers = []
        for line in file_lines:
            if "Relative Power. . . . . . .PERCTP" in line:
                p1 = line.index("PERCTP")
                p2 = line.index("%")
                search_space = line[p1:p2]
                search_space = search_space.replace("PERCTP","")
                relative_powers.append(float(search_space))

        if not relative_powers:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return relative_powers

    @staticmethod
    def relative_flow(file_lines):
        """
        Extracts the Relative Core Flow rate from the provided simulate file lines.

        Written by Brian Andersen. 3/13/2020
        """
        relative_flows = []
        for line in file_lines:
            if "Relative Flow . . . . . .  PERCWT" in line:
                p1 = line.index("PERCWT")
                p2 = line.index("%")
                search_space = line[p1:p2]
                search_space = search_space.replace("PERCWT","")
                relative_flows.append(float(search_space))

        if not relative_flows:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return relative_flows

    @staticmethod
    def thermal_power(file_lines):
        """
        Extracts the operating thermal power in MW from the provided simulate file lines.

        Written by Brian Andersen. 3/13/2020
        """
        powers = []
        for line in file_lines:
            if "Thermal Power . . . . . . . . CTP" in line:
                elems = line.strip().split()
                spot = elems.index('MWt')
                powers.append(float(elems[spot-1]))

        if not powers:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return powers

    @staticmethod
    def core_flow(file_lines):
        """
        Returns the core coolant flow in Mlb/hr from the provided simulate file lines.

        Written by Brian Andersen. 3/13/2020
        """
        flows = []
        for line in file_lines:
            if "Core Flow . . . . . . . . . . CWT" in line:
                elems = line.strip().split()
                spot = elems.index("Mlb/hr")
                flows.append(float(elems[spot-1]))

        if not flows:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return flows

    @staticmethod
    def inlet_temperatures(file_lines):
        """
        Returns the core inlet temperatures in degrees Fahrenheit from the 
        provided simulate file lines.

        Written by Brian Andersen. 3/13/2020
        """
        temperatures = []
        for line in file_lines:
            if "Inlet . . . .TINLET" in line:
                p1 = line.index("K")
                p2 = line.index("F")
                search_space = line[p1:p2]
                search_space = search_space.replace("K","")
                temperatures.append(float(search_space))

        if not temperatures:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return temperatures

    @staticmethod
    def pressure(file_lines):
        """
        Returns the core exit pressure in PSIA.

        Written by Brian Andersen. 3/13/2020
        """
        pressure = []
        for line in file_lines:
            if "Core Exit Pressure  . . . . .  PR" in line:
                p1 = line.index("bar")
                p2 = line.index("PSIA")
                search_space = line[p1:p2]
                search_space = search_space.replace("bar","")
                pressure.append(float(search_space))

        if not pressure:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return pressure

    @staticmethod
    def burnup_list(file_lines):
        """
        Extracts the cycle burnups at a each state point within the depletion.

        Written by Brian Andersen. 3/13/2020
        """
        burnups = []
        for line in file_lines:
            if "Cycle Exp." in line:
                elems = line.strip().split()
                spot = elems.index('GWd/MT')
                burnups.append(float(elems[spot-1]))

        if not burnups:
            return ValueError("No values returned. Check Simulate File executed correctly")
        else:
            return burnups

class File_Writer(object):
    """
    Class for writing and performing all tasks related to writing Simulate
    Input Files. 

    Written by Brian Andersen. 1/8/2018
    """
    @staticmethod
    def cms_link_file(casmo_list,solution_name):
        """
        Write CMS Link file for generating cross section library. Mostly used
        for assembly optimization design. Doesn't need to be used when optimizing
        a core loading pattern assuming you are using a specific set of cross 
        sections.

        Parameters
            casmo_list: List of the casmo cax files that are to be used to generate
                the cross section library. 
            solution_name: The name of the solution that will be used as the 
                name of the cms link input file. 

        Written by Brian Andersen. 1/9/2020
        """
        infile = open("genome_key",'rb')
        genome_key = pickle.load(infile)
        infile.close()

        used_genome_list = []

        cms_file = open("{}/{}_cms.inp".format(solution_name,solution_name),'w')
        cms_file.write("'COM' {} Cross Section Library\n".format(solution_name))
        cms_file.write("'NEW' '{}.lib'/\n".format(solution_name))
        for casmo in casmo_list:
            if casmo not in used_genome_list:
                if 'reflector' in genome_key[casmo]:
                    cms_file.write("'CAS' '{}' ,,, '{}'/\n".format(casmo,genome_key[casmo]['reflector']))
                    cms_file.write("'STA'/\n")
                    used_genome_list.append(casmo)
        cms_file.write("'END' /\n")
        for casmo in casmo_list:
            if casmo not in used_genome_list:
                if 'reflector' not in genome_key[casmo]:
                    cms_file.write("'CAS' '{}' '{}'/\n".format(casmo,genome_key[casmo]['marker']))
                    cms_file.write("'STA'/\n")
                    used_genome_list.append(casmo)
        cms_file.write("'END' /\n")
        cms_file.close()

    @staticmethod
    def bwr_assembly(genome,solution_name):
        """
        Writes single assembly Simulate Input File. Writes both the CMSLink
        cross section file, then the simulate input file

        Parameters:
            genome: list
            The solution genome that is to be evaluated.

            solution_name: str
            The name of the solution. Forms the directory name and input 
            file names.

        Written by Brian Andersen. 1/8/2020
        """
        infile = open("simulate_data",'rb') #Information not carried by optimization 
        simulate_data = pickle.load(infile) #solutions that is needed to fully write a 
        infile.close()                      #simulate input file.

        infile = open("genome_key",'rb') #The genome key is how the genome used by the
        genome_key = pickle.load(infile) #optimization algorithm is decoded into the 
        infile.close()                   #true solution.

        genome_dictionary = {}
        genome_dictionary['reflectors'] = {}
        genome_dictionary['fuel_segments'] = {}
        genome_dictionary['reflectors']['name'] = []
        genome_dictionary['reflectors']['count'] = []
        genome_dictionary['fuel_segments']['name'] = []
        genome_dictionary['fuel_segments']['count'] = []

        gene_set = set(genome)

        for gene in gene_set:
            if 'reflector' in genome_key[gene]:
                genome_dictionary['reflectors']['name'].append(genome_key[gene]['reflector'])
            else:
                genome_dictionary['fuel_segments']['name'].append(gene)

        current_count = 1
        for foo in genome_dictionary['reflectors']['name']:
            if current_count < 10:
                current_string = "0{}".format(current_count)
            else:
                current_string = "{}".format(current_count)
            genome_dictionary['reflectors']['count'].append(current_string)
            current_count +=1

        for foo in genome_dictionary['fuel_segments']['name']:
            if current_count < 10:
                current_string = "0{}".format(current_count)
            else:
                current_string = "{}".format(current_count)
            genome_dictionary['fuel_segments']['count'].append(current_string)
            current_count +=1

        sim_file = open("{}/{}_sim.inp".format(solution_name,solution_name),'w')
        sim_file.write("'COM' Optimimzation Case {}\n".format(solution_name))
        sim_file.write("\n")
        sim_file.write("'DIM.BWR' 2 1 2/\n")
        sim_file.write("'DIM.CAL' {} 4 1 0/\n".format(simulate_data['axial_nodes']))
        sim_file.write("'DIM.DEP' ")
        for par in simulate_data['depletion']['parameters']: #par is short for parameters
            sim_file.write("'{}' ".format(par))
        sim_file.write("/\n\n")
        sim_file.write("'TIT.PRO' 'Single Assembly Simulate BWR' / \n")
        sim_file.write("'TIT.RUN' '{}'/\n".format(solution_name))
        sim_file.write("'TIT.CAS' 'Optimization Solution {}'/\n".format(solution_name))
        sim_file.write("\n")
        sim_file.write("'LIB' '{}.lib' / \n".format(solution_name))
        sim_file.write("\n")
        sim_file.write("'COR.DAT' {}".format(simulate_data['width']))
        sim_file.write(" {} {}".format(simulate_data['height'],simulate_data['power']['value']))
        sim_file.write(" {}/\n".format(simulate_data['flow_rate']['value']))
        sim_file.write("'COR.OPE' {} {}".format(simulate_data['power']['rate'],simulate_data['flow_rate']['rate']))
        sim_file.write(" {}/\n".format(simulate_data['pressure']))
        sim_file.write("'COR.SUB' {}/\n".format(simulate_data['inlet']))
        sim_file.write("'COR.SYM' 'MIR' 1 1 1 1/\n\n")
        first_post = True

        for i,j in zip(genome_dictionary['reflectors']['count'],genome_dictionary['reflectors']['name']):
            if first_post:
                sim_file.write("'REF.LIB' ,{} '{}'/\n".format(i,j))
                first_post = False
            else:
                sim_file.write("          ,{} '{}'/\n".format(i,j))
        first_post = True
        for i,j in zip(genome_dictionary['fuel_segments']['count'],genome_dictionary['fuel_segments']['name']):
            if first_post:
                sim_file.write("'SEG.LIB' ,{} '{}'/\n".format(i,genome_key[j]['marker']))
                first_post = False
            else:
                sim_file.write("          ,{} '{}'/\n".format(i,genome_key[j]['marker']))
        sim_file.write("\n")
        sim_file.write("'SEG.TFU' 0  0.0  290.0  0.0/\n")
        sim_file.write("'CRD.BNK'  48 /\n")
        sim_file.write("'FUE.ZON' ,1 1 'FUE1' 01 0.0 ") 
        #Genome Size of 10 is Hard Coded into the optimization for the moment.
        #I don't currently have time to figure out a system for various sized
        #genomes.
        ind = genome_dictionary['fuel_segments']['name'].index(genome[1])
        sim_file.write("{} 47.625 ".format(genome_dictionary['fuel_segments']['count'][ind])) 
        ind = genome_dictionary['fuel_segments']['name'].index(genome[2])
        sim_file.write("{} 95.25 ".format(genome_dictionary['fuel_segments']['count'][ind])) 
        ind = genome_dictionary['fuel_segments']['name'].index(genome[3])
        sim_file.write("{} 142.875 ".format(genome_dictionary['fuel_segments']['count'][ind])) 
        ind = genome_dictionary['fuel_segments']['name'].index(genome[4])
        sim_file.write("{} 190.5 ".format(genome_dictionary['fuel_segments']['count'][ind])) 
        ind = genome_dictionary['fuel_segments']['name'].index(genome[5])
        sim_file.write("{} 238.125 ".format(genome_dictionary['fuel_segments']['count'][ind])) 
        ind = genome_dictionary['fuel_segments']['name'].index(genome[6])
        sim_file.write("{} 285.75 ".format(genome_dictionary['fuel_segments']['count'][ind])) 
        ind = genome_dictionary['fuel_segments']['name'].index(genome[7])
        sim_file.write("{} 333.375 ".format(genome_dictionary['fuel_segments']['count'][ind])) 
        ind = genome_dictionary['fuel_segments']['name'].index(genome[8])
        sim_file.write("{} 381.0 ".format(genome_dictionary['fuel_segments']['count'][ind])) 
        sim_file.write("02/ \n")
        sim_file.write("'FUE.TYP' 1\n")
        sim_file.write("          1 1\n")
        sim_file.write("          1 1/\n")
        sim_file.write("'HYD.ISO'/\n")
        sim_file.write("'PRI.STA' ")
        for foo in simulate_data['print_statements']:
            sim_file.write("'{}' ".format(foo))
        sim_file.write("/\n")
        sim_file.write("'PRI.INP' 'FULL'/\n")
        sim_file.write("'DEP.CYC' 'CYCLE01' 0.0, 01/\n")
        sim_file.write("'DEP.STA' 'AVE' 0.0, -{}, {}/\n".format(simulate_data['depletion']['timestep'],simulate_data['depletion']['exposure']))
        sim_file.write("'PIN.EDT' 'ON' ")
        for i in simulate_data['pin_edits']:
            sim_file.write("'{}' ".format(i))
        sim_file.write("/\n")
        sim_file.write("'PIN.EXP' ")
        for i in simulate_data['exposure_states']:
            sim_file.write("{} ".format(i))
        sim_file.write("/\n")
        sim_file.write("'PIN.ASM' 'ALL-3D'/\n")
        sim_file.write("'PIN.ZED' {}*1/\n".format(simulate_data['axial_nodes']))
        sim_file.write("'STA'/\n")
        sim_file.write("'END'/\n")
        sim_file.close()

    @staticmethod
    def pwr_assembly(genome,solution_name):
        """
        Writes single assembly Simulate Input File. Writes both the CMSLink
        cross section file, then the simulate input file.
        """
        cms_file = open(solution_name+"_cms.inp",'w')
        cms_file.write("'COM' '{}' /\n".format(solution_name))
        cms_file.write("'NEW' {}.lib /\n".format(solution_name))
        for gene in genome:
            cms_file.write("'CAS' 'Casmo_Solutions/{}' /\n".format(gene))
            cms_file.write("'STA' /\n")
        cms_file.write("'END' /\n")
        cms_file.close()

        sim_file = open(solution_name+"_sim.inp",'w')
        sim_file.write("'COM' Optimimzation Case\n")
        sim_file.write("\n")
        sim_file.write("'DIM.BWR' 1/\n")
        sim_file.write("'DIM.CAL' 24, 4 /\n")
        sim_file.write("'DIM.DEP' 'EXP' 'PIN' 'EBP' /\n")
        sim_file.write("\n")
        sim_file.write("'TIT.PRO' '{}' / \n".format(solution_name))
        sim_file.write("\n")
        sim_file.write("'LIB' '{}.lib' / \n".format(solution_name))
        sim_file.write("\n")
        sim_file.write("'REF.LIB' ,01 'BOTREF'/\n")
        sim_file.write("          ,02 'TOPREF'/\n")
        sim_file.write("'SEG.LIB' ,03 'TYPE1'/\n")
        sim_file.write("          ,04 'TYPE2'/\n")
        sim_file.write("          ,05 'TYPE3'/\n")
        sim_file.write("          ,06 'TYPE4'/\n")
        sim_file.write("          ,07 'TYPE5'/\n")
        sim_file.write("          ,08 'TYPE6'/\n")
        sim_file.write("          ,09 'TYPE7'/\n")
        sim_file.write("          ,10 'TYPE8'/\n")
        sim_file.write("'SEG.TFU' 0  0.0  290.0  0.0/\n")
        sim_file.write("'FUE.ZON ,1 1 'FUE1' 01 0.0 03 15.24 04 67.49 05 119.74 06 171.99 07 224.24 08 276.49 09 328.74 ")
        sim_file.write("10 381.0 02/ \n")
        sim_file.write("'FUE.TYP'  ,1  1  ")
        sim_file.write("'HYD.ISO/\n")
        sim_file.write("'PIN.EDT' 'ON' 'SUMM' '3PIN' / \n")
        sim_file.write("'STA'/\n")

    @staticmethod
    def write_input_file(solution):
        """
        Writes the input files for the reactor core.
        """
        file_ = open("genome_key",'rb')
        genome_key = pickle.load(file_)
        file_.close()

        if solution.batch_number <=1:
            loading_pattern = File_Writer.serial_loading_pattern(solution,genome_key)
        else:
            loading_pattern = File_Writer.label_loading_pattern(solution,genome_key)

        os.system(f"mkdir {solution.name}")
        os.system(f"cp {solution.library} {solution.name}/")
        file_ = open(f"{solution.name}/{solution.name}_sim.inp",'w')
        if solution.batch_number <= 1:
            file_.write(f"'RES' '../{solution.restart_file}' {solution.load_point}/\n")
        else:
            file_.write(f"'DIM.PWR' {solution.core_width}/\n")
            file_.write(f"'DIM.CAL' {solution.axial_nodes} 2 2/\n")
            file_.write("'DIM.DEP' 'EXP' 'PIN' 'HTMO' 'HBOR' 'HTF' 'XEN' 'SAM'/     \n")
        file_.write("\n")
        file_.write(loading_pattern)
        file_.write("\n")
        if solution.batch_number <=1:
            pass
        else:
            file_.write(f"'RES' '../{solution.restart_file}' {solution.load_point}/\n")
            for i,seg in enumerate(solution.fuel_segments):
                if not i:
                    file_.write(f"'SEG.LIB'  ,{seg} '{solution.fuel_segments[seg]}'/ \n")
                else:
                    file_.write(f"           ,{seg} '{solution.fuel_segments[seg]}'/ \n")
        file_.write(f"'COR.OPE' {solution.power}, {solution.flow}, {solution.pressure}/\n")
        file_.write("'COR.TIN' {}/ \n".format(solution.inlet_temperature))
        file_.write("\n")
        if solution.batch_number >= 2:
            file_.write(f"'BAT.LAB' {solution.batch_number} 'CYC-{solution.batch_number}' /\n")
            file_.write(f"'DEP.CYC' 'CYCLE{solution.batch_number}' 0.0 {solution.batch_number}/\n")
        file_.write(f"'DEP.STA' 'AVE' 0.0 0.5 1 2 -1 {solution.depletion} /\n")
        file_.write("'COM' The following performs an automated search on cycle length at a boron concentration of 10 ppm\n")
        file_.write("'ITE.SRC' 'SET' 'EOLEXP' , , 0.02, , , , , , 'MINBOR' 10., , , , , 4, 4, , , /\n")
        if not solution.core_edits: 
            pass
        else:
            line = "'PRI.STA' "
            assembly_edits = ('2EXP','2RPF')
            pin_edits = ('3PIN','3PXP','3KWF')
            for edit in solution.core_edits:
                if edit in assembly_edits:
                    line += f"{edit} "
                file_.write(line+"/\n")
            line = "'PIN.EDT' 'ON' "
            for edit in solution.core_edits:
                if edit in pin_edits:
                    line += f"{edit} "
            file_.write(line+ "/\n")
            file_.write("'PIN.ASM' 'ALL-3D'/\n")
        file_.write("'STA'/\n")
        file_.write("'END'/\n")
        file_.close()

    @staticmethod
    def return_core_blueprint(solution):
        """
        Returns the appropriate core map type for the optimization problem
        based on the provided solution.
        """
        if solution.map_size.lower() == "full_core" or solution.map_size.lower() == "full":
            map_key = "FULL"
            allowed_symmetries = ("OCTANT","QUARTER_ROTATIONAL","QUARTER_MIRROR")
            if solution.symmetry.upper() in allowed_symmetries:
                symmetry_key = solution.symmetry.upper()
            else:
                ValueError(f"Unrecognized problem symmetry. Recognized symmetries are {allowed_symmetries}")
        elif solution.map_size.lower() == "quarter" or solution.map_size.lower() == "quarter_core":
            map_key = "QUARTER"
            allowed_symmetries = ("OCTANT","QUARTER")
            if solution.symmetry.upper() in allowed_symmetries:
                symmetry_key = solution.symmetry.upper()
            else:
                ValueError(f"Unrecognized problem symmetry. Recognized symmetries are {allowed_symmetries}")
        else:
            ValueError("Unrecognized core map key.")

        if solution.reflector_present:
            refl_key = "WITH_REFLECTOR"
        else:
            refl_key = "WITHOUT_REFLECTOR"

        return CORE_MAPS[map_key][symmetry_key][solution.number_assemblies][refl_key]

    @staticmethod
    def serial_loading_pattern(solution,genome_key):
        """
        Writes a core loading pattern using serial numbers as the loading
        pattern designator.

        Written by Brian Andersen 4/5/2020
        """
        biggest_number = 0
        for gene in genome_key:
            if gene == "additional_information" or gene == 'symmetry_list':
                pass
            else:
                if genome_key[gene]['type'] > biggest_number:
                    biggest_number = genome_key[gene]['type']
        
        number_spaces = len(str(biggest_number)) + 1
        problem_map = File_Writer.return_core_blueprint(solution) 

        row_count = 1
        loading_pattern = ""
        for row in range(25):    #I doubt a problem will ever be larger than a 25 by 25 core
            if row in problem_map:                 #it will just work
                loading_pattern += f"'FUE.TYP'  {row_count},"
                for col in range(25):#so I hard coded the value because if I did this algorithm right  
                    if col in problem_map[row]:
                        if not problem_map[row][col]:
                            if type(problem_map[row][col]) == int:
                                gene_number = problem_map[row][col]
                                gene = solution.genome[gene_number]
                                value = genome_key[gene]['type']
                                str_ = f"{value}"
                                loading_pattern += f"{str_.rjust(number_spaces)}"
                            else:
                                loading_pattern += f"{'0'.rjust(number_spaces)}"
                        else:
                            gene_number = problem_map[row][col]
                            gene = solution.genome[gene_number]
                            value = genome_key[gene]['type']
                            str_ = f"{value}"
                            loading_pattern += f"{str_.rjust(number_spaces)}"
                loading_pattern += "/\n"
                row_count += 1

        loading_pattern += "\n"

        return loading_pattern

    @staticmethod
    def label_loading_pattern(solution,genome_key):
        """
        Writes a core loading pattern using assembly type as the loading
        pattern designator.

        Written by Brian Andersen 4/5/2020
        """
        biggest_number = 0
        pass_set = set(['additional_information','symmetry_list'])
        for gene in genome_key:
            if gene in pass_set:
                pass
            else:
                if type(genome_key[gene]['type']) == list:
                    pass
                else:
                    if genome_key[gene]['type'] > biggest_number:
                        biggest_number = genome_key[gene]['type']
        largest_label = f"TYPE{biggest_number}"
        magnitude = len(largest_label) #Pop Pop

        blank = ""
        for l in largest_label:
            blank += " "
        problem_map = File_Writer.return_core_blueprint(solution) 

        loading_pattern = f"'FUE.LAB',{len(largest_label)}/\n"
        count_dictionary = {}
        for row in range(25):
            if row in problem_map:
                if row+1 < 10:
                    loading_pattern += f"{row+1}   1 "
                else:
                    loading_pattern += f"{row+1}  1 "
                for col in range(25):
                    if col in problem_map[row]:
                        if not problem_map[row][col]:
                            if type(problem_map[row][col]) == int:
                                gene_number = problem_map[row][col]
                                gene = solution.genome[gene_number]
                                if type(genome_key[gene]['type']) == list:
                                    value = genome_key[gene]['type'].pop()
                                    if len(value) < 4:
                                        print(f"WARNING: You probably left the zero out of the assembly position for {value}.")
                                        print("Simulate Run May FAIL.")
                                else:
                                    value = str(genome_key[gene]['type'])
                                    if len(value) == 1:
                                        value = value = f"TYPE0{value}"
                                    else: 
                                        value = f"TYPE{value}"
                                    if gene in count_dictionary:
                                        count_dictionary[gene]+=1
                                    else:
                                        count_dictionary[gene] = 1
                                loading_pattern += f"{value.ljust(magnitude)} "
                            else:
                                loading_pattern += f"{blank} "
                        else:
                            gene_number = problem_map[row][col]
                            gene = solution.genome[gene_number]
                            if type(genome_key[gene]['type']) == list:
                                value = genome_key[gene]['type'].pop()
                                if len(value) < 4:
                                    print(f"WARNING: You probably left the zero out of the assembly position for {value}.")
                                    print("Simulate Run May FAIL.")
                            else:
                                value = str(genome_key[gene]['type'])
                                if len(value) == 1:
                                    value = value = f"TYPE0{value}"
                                else: 
                                    value = f"TYPE{value}"
                                if gene in count_dictionary:
                                    count_dictionary[gene]+=1
                                else:
                                    count_dictionary[gene] = 1
                            loading_pattern += f"{value.ljust(magnitude)} "
                loading_pattern += "\n"
        loading_pattern += "0    0\n\n"
        for gene in count_dictionary:
            foo = str(genome_key[gene]['type'])
            if len(foo) == 1:
                loading_pattern += f"'FUE.NEW', 'TYPE0{genome_key[gene]['type']}', {genome_key[gene]['serial']}, "
            else:
                loading_pattern += f"'FUE.NEW', 'TYPE{genome_key[gene]['type']}', {genome_key[gene]['serial']}, "
            loading_pattern += f"{count_dictionary[gene]}, {genome_key[gene]['type']},,,{solution.batch_number}/\n"

        loading_pattern += "\n"
        return loading_pattern

class Calculator(object):
    """
    Object for calculating various parameters such as the Boiling Transition
    Factor or other values. Basically if you have to do math, stick the
    method in this class.

    Written by Brian Andersen. 1/8/2020
    """
    @staticmethod
    def calculate_BTF(power_dictionary,assem_type):
        """
        Calculates the boiling transition factor for a Boiling Water Reactor assembly. Currently only BWR
        10x10 fuel assemblies are supported. 

        Parameters:
            power_dicionary: Dictionary of the assembly pin powers.
            assem_type: The assembly type being used, designating which
                additive constants are to be used in calculating the BTF 
                factor.

        Written by Brian Andersen. 1/9/2020
        """
        if assem_type == 'GE14':
            num_rows = 10
            num_cols = 10
            additive_constant = numpy.array([[-0.061,-0.078,-0.084,-0.083,-0.073,-0.074,-0.095,-0.084,-0.104,-0.086],
                                             [-0.078, 0.450,-0.016, 0.450,-0.007,-0.003, 0.450,-0.055, 0.450,-0.116],
                                             [-0.084,-0.016,-0.025, 0.005,-0.003,-0.031,-0.049,-0.020,-0.066,-0.113],
                                             [-0.083, 0.450, 0.005,-0.008,-0.011, 0.000, 0.000,-0.058, 0.450,-0.134],
                                             [-0.073,-0.007,-0.003,-0.011, 0.450, 0.000, 0.000,-0.041,-0.043,-0.122],
                                             [-0.074,-0.003,-0.031, 0.000, 0.000, 0.450,-0.022,-0.041,-0.042,-0.127],
                                             [-0.095, 0.450,-0.049, 0.000, 0.000,-0.022,-0.023,-0.031, 0.450,-0.148],
                                             [-0.084,-0.055,-0.020,-0.058,-0.041,-0.041,-0.031,-0.042,-0.083,-0.138],
                                             [-0.104, 0.450,-0.066, 0.450,-0.043,-0.042, 0.450,-0.083, 0.450,-0.150],
                                             [-0.086,-0.116,-0.113,-0.134,-0.122,-0.127,-0.148,-0.138,-0.150,-0.131]])
        
        elif assem_type == 'GNF2':
            num_rows = 10
            num_cols = 10
            additive_constant = numpy.array([[-0.15,-0.12,-0.12,-0.12,-0.12,-0.12,-0.12,-0.12,-0.12,-0.15],
                                             [-0.12,-0.05,-0.05,-0.05,-0.05,-0.05,-0.05,-0.05,-0.05,-0.12],
                                             [-0.12,-0.05,-0.05,-0.05,-0.05,-0.05,-0.05,-0.05,-0.05,-0.12],
                                             [-0.12,-0.05,-0.05,-0.05,-0.08,-0.08,-0.08,-0.05,-0.05,-0.12],
                                             [-0.12,-0.05,-0.05,-0.08,-0.00,-0.00,-0.00,-0.08,-0.05,-0.12],
                                             [-0.12,-0.05,-0.05,-0.08,-0.00,-0.00,-0.00,-0.10,-0.05,-0.12],
                                             [-0.12,-0.05,-0.05,-0.08,-0.00,-0.00,-0.00,-0.09,-0.05,-0.12],
                                             [-0.12,-0.05,-0.05,-0.05,-0.08,-0.10,-0.09,-0.05,-0.05,-0.12],
                                             [-0.12,-0.05,-0.05,-0.05,-0.05,-0.05,-0.05,-0.05,-0.05,-0.12],
                                             [-0.15,-0.12,-0.12,-0.12,-0.12,-0.12,-0.12,-0.12,-0.12,-0.12]])
        weight_side = 0.2
        weight_corner = 0.05

        key_list = list(power_dictionary.keys())
        key = key_list[0]

        maximum_btf = 0.00
        btf_matrix_list = []
        for burnup in power_dictionary[key]:
            integrated_matrix = numpy.zeros(shape=(num_rows,num_cols))
            pin_count = 0
            for i in range(num_rows):
                for j in range(num_cols):
                    for height in power_dictionary[key][burnup]:
                        integrated_matrix[i][j] += power_dictionary[key][burnup][height][pin_count]
                    pin_count += 1
            integrated_matrix /= float(len(power_dictionary[key][burnup]))
       #     integrated_matrix = numpy.sqrt(integrated_matrix)
            corner_matrix = numpy.zeros(shape=(num_rows,num_cols))
            side_matrix   = numpy.zeros(shape=(num_rows,num_cols))
            corner_count_matrix = numpy.zeros(shape=(num_rows,num_cols))
            side_count_matrix   = numpy.zeros(shape=(num_rows,num_cols))
            for i in range(num_rows):
                for j in range(num_cols):
                    if integrated_matrix[i,j] > 0.00:
                        if i-1 >= 0:
                            side_matrix[i,j] += integrated_matrix[i-1,j]
                            side_count_matrix[i,j] +=1
                            if j-1>=0:
                                corner_matrix[i,j] += integrated_matrix[i-1,j-1]
                                corner_count_matrix[i,j] +=1
                            if j+1 < num_cols:
                                corner_matrix[i,j] += integrated_matrix[i-1,j+1]
                                corner_count_matrix[i,j] += 1
                        if i+1 < num_rows:
                            side_matrix[i,j] += integrated_matrix[i+1,j]
                            side_count_matrix[i,j] += 1
                            if j-1>=0:
                                corner_matrix[i,j] += integrated_matrix[i+1,j-1]
                                corner_count_matrix[i,j] +=1
                            if j+1 < num_cols:
                                corner_matrix[i,j] += integrated_matrix[i+1,j+1]
                                corner_count_matrix[i,j] += 1
                        if j-1>=0:
                            side_matrix[i,j] += integrated_matrix[i,j-1]
                            side_count_matrix[i,j] +=1
                        if j+1 < num_cols:
                            side_matrix[i,j] += integrated_matrix[i,j+1]
                            side_count_matrix[i,j] += 1
            integrated_matrix = numpy.sqrt(integrated_matrix)
            side_matrix = numpy.sqrt(side_matrix)
            corner_matrix = numpy.sqrt(corner_matrix)
            numerator = integrated_matrix + weight_side*side_matrix + weight_corner*corner_matrix
            denominator = 1 + weight_side*side_matrix + weight_corner*corner_matrix
            btf_matrix = numpy.divide(numerator,denominator) + additive_constant
            btf_matrix_list.append(btf_matrix)
            if maximum_btf < numpy.max(btf_matrix):
                maximum_btf = numpy.max(btf_matrix)

        return btf_matrix_list,maximum_btf

###########################################################################################################################################
#CORE MAPS
##############################################################################################################################################
CORE_MAPS = {}
CORE_MAPS['FULL'] = {}
CORE_MAPS['FULL']['OCTANT'] = {}
CORE_MAPS['FULL']['OCTANT'][157] = {}
CORE_MAPS['FULL']['OCTANT'][157]['WITH_REFLECTOR'] = { 0:{0:None,1:None,2:None,3:None,4:None,5:None,6:34,7:33,8:32,9:33,10:34,11:None,12:None,13:None,14:None, 15:None,16:None},
                                                       1:{0:None,1:None,2:None,3:None,4:31  ,5:30,  6:29,7:28,8:27,9:28,10:29,11:30,  12:31,  13:None,14:None, 15:None,16:None},
                                                       2:{0:None,1:None,2:None,3:26  ,4:25  ,5:24,  6:23,7:22,8:21,9:22,10:23,11:24,  12:25,  13:26,  14:None, 15:None,16:None},
                                                       3:{0:None,1:None,2:26  ,3:20  ,4:19  ,5:18,  6:17,7:16,8:15,9:16,10:17,11:18,  12:19,  13:20,  14:26  , 15:None,16:None},
                                                       4:{0:None,1:31,  2:25  ,3:19  ,4:14  ,5:13,  6:12,7:11,8:10,9:11,10:12,11:13,  12:14,  13:19,  14:25  , 15:31,  16:None},
                                                       5:{0:None,1:30,  2:24  ,3:18  ,4:13  ,5:9,   6:8, 7:7, 8:6, 9:7, 10:8, 11:9,   12:13,  13:18,  14:24  , 15:30,  16:None},
                                                       6:{0:34,  1:29,  2:23  ,3:17  ,4:12  ,5:8,   6:5, 7:4, 8:3, 9:4, 10:5, 11:8,   12:12,  13:17,  14:23  , 15:29,  16:34},
                                                       7:{0:33,  1:28,  2:22  ,3:16  ,4:11  ,5:7,   6:4, 7:2, 8:1, 9:2, 10:4, 11:7,   12:11,  13:16,  14:22  , 15:28,  16:33},
                                                       8:{0:32,  1:27,  2:21  ,3:15  ,4:10  ,5:6,   6:3, 7:1, 8:0, 9:1, 10:3, 11:6,   12:10,  13:15,  14:21  , 15:27,  16:32},
                                                       9:{0:33,  1:28,  2:22  ,3:16  ,4:11  ,5:7,   6:4, 7:2, 8:1, 9:2, 10:4, 11:7,   12:11,  13:16,  14:22  , 15:28,  16:33},
                                                      10:{0:34,  1:29,  2:23  ,3:17  ,4:12  ,5:8,   6:5, 7:4, 8:3, 9:4, 10:5, 11:8,   12:12,  13:17,  14:23  , 15:29,  16:34},
                                                      11:{0:None,1:30,  2:24  ,3:18  ,4:13  ,5:9,   6:8, 7:7 ,8:6, 9:7, 10:8, 11:9,   12:13,  13:18,  14:24  , 15:30,  16:None},
                                                      12:{0:None,1:31,  2:25  ,3:19  ,4:14  ,5:13,  6:12,7:11,8:10,9:11,10:12,11:13,  12:14,  13:19,  14:25  , 15:31,  16:None},
                                                      13:{0:None,1:None,2:26  ,3:20  ,4:19  ,5:18,  6:17,7:16,8:15,9:16,10:17,11:18,  12:19,  13:20,  14:26  , 15:None,16:None},
                                                      14:{0:None,1:None,2:None,3:26  ,4:25  ,5:24,  6:23,7:22,8:21,9:22,10:23,11:24,  12:25,  13:26,  14:None, 15:None,16:None},
                                                      15:{0:None,1:None,2:None,3:None,4:31  ,5:30,  6:29,7:28,8:27,9:28,10:29,11:30,  12:31,  13:None,14:None, 15:None,16:None},
                                                      16:{0:None,1:None,2:None,3:None,4:None,5:None,6:34,7:33,8:32,9:33,10:34,11:None,12:None,13:None,14:None, 15:None,16:None}}
CORE_MAPS['FULL']['OCTANT'][157]['WITHOUT_REFLECTOR'] = { 0:{0:None,1:None,2:None,3:None,4:None,5:None,6:25,7:24,8:25,9:None,10:None,11:None,12:None,13:None,14:None},
                                                          1:{0:None,1:None,2:None,3:None,4:23,  5:22,  6:21,7:20,8:21,9:22,  10:23,  11:None,12:None,13:None,14:None},
                                                          2:{0:None,1:None,2:None,3:19,  4:18,  5:17,  6:16,7:15,8:16,9:17,  10:18,  11:19,  12:None,13:None,14:None},
                                                          3:{0:None,1:None,2:19,  3:14,  4:13,  5:12,  6:11,7:10,8:11,9:12,  10:13,  11:14,  12:19,  13:None,14:None},
                                                          4:{0:None,1:23,  2:18,  3:13,  4:9,   5:8,   6:7, 7:6, 8:7, 9:8,   10:9,   11:13,  12:18,  13:23,  14:None},
                                                          5:{0:None,1:22,  2:17,  3:12,  4:8,   5:5,   6:4, 7:3, 8:4, 9:5,   10:8,   11:12,  12:17,  13:22,  14:None},
                                                          6:{0:25,  1:21,  2:16,  3:11,  4:7,   5:4,   6:2, 7:1, 8:2, 9:4,   10:7,   11:11,  12:16,  13:21,  14:25},
                                                          7:{0:24,  1:20,  2:15,  3:10,  4:6,   5:3,   6:1, 7:0, 8:1, 9:3,   10:6,   11:10,  12:15,  13:20,  14:24},
                                                          8:{0:25,  1:21,  2:16,  3:11,  4:7,   5:4,   6:2, 7:1, 8:2, 9:4,   10:7,   11:11,  12:16,  13:21,  14:25},
                                                          9:{0:None,1:22,  2:17,  3:12,  4:8,   5:5,   6:4, 7:3, 8:4, 9:5,   10:8,   11:12,  12:17,  13:22,  14:None},
                                                         10:{0:None,1:23,  2:18,  3:13,  4:9,   5:8,   6:7, 7:6, 8:7,9:8,    10:9 ,  11:13,  12:18,  13:23,  14:None},
                                                         11:{0:None,1:None,2:19,  3:14,  4:13,  5:12,  6:11,7:10,8:11,9:12,  10:13,  11:14,  12:19,  13:None,14:None},
                                                         12:{0:None,1:None,2:None,3:19,  4:18,  5:17,  6:16,7:15,8:16,9:17,  10:18,  11:19,  12:None,13:None,14:None},
                                                         13:{0:None,1:None,2:None,3:None,4:23,  5:22,  6:21,7:20,8:21,9:22,  10:23,  11:None,12:None,13:None,14:None},
                                                         14:{0:None,1:None,2:None,3:None,4:None,5:None,6:25,7:24,8:25,9:None,10:None,11:None,12:None,13:None,14:None}}
CORE_MAPS['FULL']['OCTANT'][193] = {}
CORE_MAPS['FULL']['OCTANT'][193]['WITH_REFLECTOR'] = {0:{0:None,1:None,2:None,3:None,4:39,5:38,6:37,7:36,8:35,9:36,10:37,11:38,12:39,13:None,14:None,15:None,16:None},
                                                      1:{0:None,1:None,2:34,  3:33,  4:32,5:31,6:30,7:29,8:28,9:29,10:30,11:31,12:32,13:33,  14:34,  15:None,16:None},
                                                      2:{0:None,1:34,  2:27,  3:26,  4:25,5:24,6:23,7:22,8:21,9:22,10:23,11:24,12:25,13:26,  14:27,  15:34,  16:None},
                                                      3:{0:None,1:33,  2:26,  3:20,  4:19,5:18,6:17,7:16,8:15,9:16,10:17,11:18,12:19,13:20,  14:26,  15:33,  16:None},
                                                      4:{0:39,  1:32,  2:25,  3:19,  4:14,5:13,6:12,7:11,8:10,9:11,10:12,11:13,12:14,13:19,  14:25,  15:32,  16:39},
                                                      5:{0:38,  1:31,  2:24,  3:18,  4:13,5:9, 6:8, 7:7, 8:6, 9:7, 10:8, 11:9, 12:13,13:18,  14:24,  15:31,  16:38},
                                                      6:{0:37,  1:30,  2:23,  3:17,  4:12,5:8, 6:5, 7:4, 8:3, 9:4, 10:5, 11:8, 12:12,13:17,  14:23,  15:30,  16:37},
                                                      7:{0:36,  1:29,  2:22,  3:16,  4:11,5:7, 6:4, 7:2, 8:1, 9:2, 10:4, 11:7, 12:11,13:16,  14:22,  15:29,  16:36},
                                                      8:{0:35,  1:28,  2:21,  3:15,  4:10,5:6, 6:3, 7:1, 8:0, 9:1, 10:3, 11:6, 12:10,13:15,  14:21,  15:28,  16:35},       #Edited input count
                                                      9:{0:36,  1:29,  2:22,  3:16,  4:11,5:7, 6:4, 7:2, 8:1, 9:2, 10:4, 11:7, 12:11,13:16,  14:22,  15:29,  16:36},
                                                     10:{0:37,  1:30,  2:23,  3:17,  4:12,5:8, 6:5, 7:4, 8:3, 9:4, 10:5, 11:8, 12:12,13:17,  14:23,  15:30,  16:37},
                                                     11:{0:38,  1:31,  2:24,  3:18,  4:13,5:9, 6:8, 7:7, 8:6, 9:7, 10:8, 11:9, 12:13,13:18,  14:24,  15:31,  16:38},
                                                     12:{0:39,  1:32,  2:25,  3:19,  4:14,5:13,6:12,7:11,8:10,9:11,10:12,11:13,12:14,13:19,  14:25,  15:32,  16:39},
                                                     13:{0:None,1:33,  2:26,  3:20,  4:19,5:18,6:17,7:16,8:15,9:16,10:17,11:18,12:19,13:20,  14:26,  15:33,  16:None},
                                                     14:{0:None,1:34,  2:27,  3:26,  4:25,5:24,6:23,7:22,8:21,9:22,10:23,11:24,12:25,13:26,  14:27,  15:34,  16:None},
                                                     15:{0:None,1:None,2:34,  3:33,  4:32,5:31,6:30,7:29,8:28,9:29,10:30,11:31,12:32,13:33,  14:34,  15:None,16:None},
                                                     16:{0:None,1:None,2:None,3:None,4:39,5:38,6:37,7:36,8:35,9:36,10:37,11:38,12:39,13:None,14:None,15:None,16:None}}

CORE_MAPS['FULL']['OCTANT'][193]['WITHOUT_REFLECTOR'] = {0:{0:None,1:None,2:None,3:None,4:30,5:29, 6:28,7:27,8:28,9:29, 10:30,11:None,12:None,13:None,14:None},
                                                         1:{0:None,1:None,2:26,  3:25,  4:24,5:23, 6:22,7:21,8:22,9:23, 10:24,11:25,  12:26,  13:None,14:None},
                                                         2:{0:None,1:26,  2:20,  3:19,  4:18,5:17, 6:16,7:15,8:16,9:17, 10:18,11:19,  12:20,  13:26,  14:None},
                                                         3:{0:None,1:25,  2:19,  3:14,  4:13,5:12, 6:11,7:10,8:11,9:12, 10:13,11:14,  12:19,  13:25,  14:None},
                                                         4:{0:30,  1:24,  2:18,  3:13,  4:9, 5:8,  6:7, 7:6, 8:7, 9:8,  10:9, 11:13,  12:18,  13:24,  14:30},
                                                         5:{0:29,  1:23,  2:17,  3:12,  4:8, 5:5,  6:4, 7:3, 8:4, 9:5,  10:8, 11:12,  12:17,  13:23,  14:29},
                                                         6:{0:28,  1:22,  2:16,  3:11,  4:7, 5:4,  6:2, 7:1, 8:2, 9:4,  10:7, 11:11,  12:16,  13:22,  14:28},
                                                         7:{0:27,  1:21,  2:15,  3:10,  4:6, 5:3,  6:1, 7:0, 8:1, 9:3,  10:6, 11:10,  12:15,  13:21,  14:27},
                                                         8:{0:28,  1:22,  2:16,  3:11,  4:7, 5:4,  6:2, 7:1, 8:2, 9:4,  10:7, 11:11,  12:16,  13:22,  14:28},
                                                         9:{0:29,  1:23,  2:17,  3:12,  4:8, 5:5,  6:4, 7:3, 8:4, 9:5,  10:8, 11:12,  12:17,  13:23,  14:29},
                                                        10:{0:30,  1:24,  2:18,  3:13,  4:9, 5:8,  6:7, 7:6, 8:7, 9:8,  10:9, 11:13,  12:18,  13:24,  14:30},
                                                        11:{0:None,1:25,  2:19,  3:14,  4:13,5:12, 6:11,7:10,8:11,9:12, 10:13,11:14,  12:19,  13:25,  14:None},
                                                        12:{0:None,1:26,  2:20,  3:19,  4:18,5:17, 6:16,7:15,8:16,9:17, 10:18,11:19,  12:20,  13:26,  14:None},
                                                        13:{0:None,1:None,2:26,  3:25,  4:24,5:23, 6:22,7:21,8:22,9:23, 10:24,11:25,  12:26,  13:None,14:None},
                                                        14:{0:None,1:None,2:None,3:None,4:30,5:29, 6:28,7:27,8:28,9:29, 10:30,11:None,12:None,13:None,14:None}}
CORE_MAPS['FULL']['OCTANT'][241] = {}
CORE_MAPS['FULL']['OCTANT'][241]['WITH_REFLECTOR'] = {0:{0:None,1:None,2:None,3:None,4:None,5:47, 6:46, 7:45, 8:44, 9:43, 10:44, 11:45, 12:46, 13:47, 14:None,15:None,16:None,17:None,18:None},
                                                      1:{0:None,1:None,2:None,3:42,  4:41,  5:40, 6:39, 7:38, 8:37, 9:36, 10:37, 11:38, 12:39, 13:40, 14:41,  15:42,  16:None,17:None,18:None},
                                                      2:{0:None,1:None,2:35,  3:34,  4:33,  5:32, 6:31, 7:30, 8:29, 9:28, 10:29, 11:30, 12:31, 13:32, 14:33,  15:34,  16:35,  17:None,18:None},
                                                      3:{0:None,1:42,  2:34,  3:27,  4:26,  5:25, 6:24, 7:23, 8:22, 9:21, 10:22, 11:23, 12:24, 13:25, 14:26,  15:27,  16:34,  17:42,  18:None},
                                                      4:{0:None,1:41,  2:33,  3:26,  4:20,  5:19, 6:18, 7:17, 8:16, 9:15, 10:16, 11:17, 12:18, 13:19, 14:20,  15:26,  16:33,  17:41,  18:None},
                                                      5:{0:47,  1:40,  2:32,  3:25,  4:19,  5:14, 6:13, 7:12, 8:11, 9:10, 10:11, 11:12, 12:13, 13:14, 14:19,  15:25,  16:32,  17:40,  18:47},
                                                      6:{0:46,  1:39,  2:31,  3:24,  4:18,  5:13, 6: 9, 7: 8, 8: 7, 9: 6, 10: 7, 11: 8, 12: 9, 13:13, 14:18,  15:24,  16:31,  17:39,  18:46},
                                                      7:{0:45,  1:38,  2:30,  3:23,  4:17,  5:12, 6: 8, 7: 5, 8: 4, 9: 3, 10: 4, 11: 5, 12: 8, 13:12, 14:17,  15:23,  16:30,  17:38,  18:45},
                                                      8:{0:44,  1:37,  2:29,  3:22,  4:16,  5:11, 6: 7, 7: 4, 8: 2, 9: 1, 10: 2, 11: 4, 12: 7, 13:11, 14:16,  15:22,  16:29,  17:37,  18:44},
                                                      9:{0:43,  1:36,  2:28,  3:21,  4:15,  5:10, 6: 6, 7: 3, 8: 1, 9: 0, 10: 1, 11: 3, 12: 6, 13:10, 14:15,  15:21,  16:28,  17:36,  18:43},
                                                     10:{0:44,  1:37,  2:29,  3:22,  4:16,  5:11, 6: 7, 7: 4, 8: 2, 9: 1, 10: 2, 11: 4, 12: 7, 13:11, 14:16,  15:22,  16:29,  17:37,  18:44},
                                                     11:{0:45,  1:38,  2:30,  3:23,  4:17,  5:12, 6: 8, 7: 5, 8: 4, 9: 3, 10: 4, 11: 5, 12: 8, 13:12, 14:17,  15:23,  16:30,  17:38,  18:45},
                                                     12:{0:46,  1:39,  2:31,  3:24,  4:18,  5:13, 6: 9, 7: 8, 8: 7, 9: 6, 10: 7, 11: 8, 12: 9, 13:13, 14:18,  15:24,  16:31,  17:39,  18:46},
                                                     13:{0:47,  1:40,  2:32,  3:25,  4:19,  5:14, 6:13, 7:12, 8:11, 9:10, 10:11, 11:12, 12:13, 13:14, 14:19,  15:25,  16:32,  17:40,  18:47},
                                                     14:{0:None,1:41,  2:33,  3:26,  4:20,  5:19, 6:18, 7:17, 8:16, 9:15, 10:16, 11:17, 12:18, 13:19, 14:20,  15:26,  16:33,  17:41,  18:None},
                                                     15:{0:None,1:42,  2:34,  3:27,  4:26,  5:25, 6:24, 7:23, 8:22, 9:21, 10:22, 11:23, 12:24, 13:25, 14:26,  15:27,  16:34,  17:42,  18:None},
                                                     16:{0:None,1:None,2:35,  3:34,  4:33,  5:32, 6:31, 7:30, 8:29, 9:28, 10:29, 11:30, 12:31, 13:32, 14:33,  15:34,  16:35,  17:None,18:None},
                                                     17:{0:None,1:None,2:None,3:42,  4:41,  5:40, 6:39, 7:38, 8:37, 9:36, 10:37, 11:38, 12:39, 13:40, 14:41,  15:42,  16:None,17:None,18:None},
                                                     18:{0:None,1:None,2:None,3:None,4:None,5:47, 6:46, 7:45, 8:44, 9:43, 10:44, 11:45, 12:46, 13:47, 14:None,15:None,16:None,17:None,18:None}}
CORE_MAPS['FULL']['OCTANT'][241]['WITHOUT_REFLECTOR'] = {0:{0:None,1:None,2:None,3:None,4:None,5:37, 6:36,  7:35,  8:34, 9:35, 10:36, 11:37, 12:None,13:None,14:None,15:None,16:None}, 
                                                         1:{0:None,1:None,2:None,3:33,  4:32,  5:31, 6:30,  7:29,  8:28, 9:29, 10:30, 11:31, 12:32,  13:33,  14:None,15:None,16:None},     
                                                         2:{0:None,1:None,2:27,  3:26,  4:25,  5:24, 6:23,  7:22,  8:21, 9:22, 10:23, 11:24, 12:25,  13:26,  14:27,  15:None,16:None},     
                                                         3:{0:None,1:33,  2:26,  3:20,  4:19,  5:18, 6:17,  7:16,  8:15, 9:16, 10:17, 11:18, 12:19,  13:20,  14:26,  15:33,  16:None},     
                                                         4:{0:None,1:32,  2:25,  3:19,  4:14,  5:13, 6:12,  7:11,  8:10, 9:11, 10:12, 11:13, 12:14,  13:19,  14:25,  15:32,  16:None},     
                                                         5:{0:37  ,1:31,  2:24,  3:18,  4:13,  5:9,  6:8,   7:7,   8:6,  9:7,  10:8,  11:9,  12:13,  13:18,  14:24,  15:31,  16:37  },
                                                         6:{0:36  ,1:30,  2:23,  3:17,  4:12,  5:8,  6:5,   7:4,   8:3,  9:4,  10:5,  11:8,  12:12,  13:17,  14:23,  15:30,  16:36  },
                                                         7:{0:35  ,1:29,  2:22,  3:16,  4:11,  5:7,  6:4,   7:2,   8:1,  9:2,  10:4,  11:7,  12:11,  13:16,  14:22,  15:29,  16:35  },
                                                         8:{0:34  ,1:28,  2:21,  3:15,  4:10,  5:6,  6:3,   7:1,   8:0,  9:1,  10:3,  11:6,  12:10,  13:15,  14:21,  15:28,  16:34  },
                                                         9:{0:35  ,1:29,  2:22,  3:16,  4:11,  5:7,  6:4,   7:2,   8:1,  9:2,  10:4,  11:7,  12:11,  13:16,  14:22,  15:29,  16:35  },
                                                        10:{0:36  ,1:30,  2:23,  3:17,  4:12,  5:8,  6:5,   7:4,   8:3,  9:4,  10:5,  11:8,  12:12,  13:17,  14:23,  15:30,  16:36  },
                                                        11:{0:37  ,1:31,  2:24,  3:18,  4:13,  5:9,  6:8,   7:7,   8:6,  9:7,  10:8,  11:9,  12:13,  13:18,  14:24,  15:31,  16:37  },
                                                        12:{0:None,1:32,  2:25,  3:19,  4:14,  5:13, 6:12,  7:11,  8:10, 9:11, 10:12, 11:13, 12:14,  13:19,  14:25,  15:32,  16:None},         
                                                        13:{0:None,1:33,  2:26,  3:20,  4:19,  5:18, 6:17,  7:16,  8:15, 9:16, 10:17, 11:18, 12:19,  13:20,  14:26,  15:33,  16:None},     
                                                        14:{0:None,1:None,2:27,  3:26,  4:25,  5:24, 6:23,  7:22,  8:21, 9:22, 10:23, 11:24, 12:25,  13:26,  14:27,  15:None,16:None},     
                                                        15:{0:None,1:None,2:None,3:33,  4:32,  5:31, 6:30,  7:29,  8:28, 9:29, 10:30, 11:31, 12:32,  13:33,  14:None,15:None,16:None},     
                                                        16:{0:None,1:None,2:None,3:None,4:None,5:37, 6:36,  7:35,  8:34, 9:35, 10:36, 11:37, 12:None,13:None,14:None,15:None,16:None}}
CORE_MAPS['FULL']['QUARTER_MIRROR'] = {}
CORE_MAPS['FULL']['QUARTER_MIRROR'][157] = {}
CORE_MAPS['FULL']['QUARTER_MIRROR'][157]['WITH_REFLECTOR'] =  {0:{0:None,1:None,2:None,3:None,4:None,5:None,6:55, 7:54, 8:53,9:54, 10:55,11:None,12:None,13:None,14:None,15:None,16:None},
                                                               1:{0:None,1:None,2:None,3:None,4:52,  5:51,  6:50, 7:49, 8:48,9:49, 10:50,11:51,  12:52,  13:None,14:None,15:None,16:None},
                                                               2:{0:None,1:None,2:None,3:47,  4:46,  5:45,  6:44, 7:43, 8:42,9:43, 10:44,11:45,  12:46,  13:47,  14:None,15:None,16:None},
                                                               3:{0:None,1:None,2:41,  3:40,  4:39,  5:38,  6:37, 7:36, 8:35,9:36, 10:37,11:38,  12:39,  13:40,  14:41,  15:None,16:None},
                                                               4:{0:None,1:34,  2:33,  3:32,  4:31,  5:30,  6:29, 7:28, 8:27,9:28, 10:29,11:30,  12:31,  13:32,  14:33,  15:34,  16:None},
                                                               5:{0:None,1:26,  2:25,  3:24,  4:23,  5:22,  6:21, 7:20, 8:19,9:20, 10:21,11:22,  12:23,  13:24,  14:25,  15:26,  16:None},
                                                               6:{0:18,  1:17,  2:16,  3:15,  4:14,  5:13,  6:12, 7:11, 8:10,9:11, 10:12,11:13,  12:14,  13:15,  14:16,  15:17,  16:18},
                                                               7:{0:9,   1:8,   2:7,   3:6,   4:5,   5:4,   6:3,  7:2,  8:1, 9:2,  10:3, 11:4,   12:5,   13:6,   14:7,   15:8,   16:9},
                                                               8:{0:53,  1:48,  2:42,  3:35,  4:27,  5:19,  6:10, 7:1,  8:0, 9:1,  10:10,11:19,  12:27,  13:35,  14:42,  15:48,  16:53},
                                                               9:{0:9,   1:8,   2:7,   3:6,   4:5,   5:4,   6:3,  7:2,  8:1, 9:2,  10:3, 11:4,   12:5,   13:6,   14:7,   15:8,   16:9},
                                                              10:{0:18,  1:17,  2:16,  3:15,  4:14,  5:13,  6:12, 7:11, 8:10,9:11, 10:12,11:13,  12:14,  13:15,  14:16,  15:17,  16:18},
                                                              11:{0:None,1:26,  2:25,  3:24,  4:23,  5:22,  6:21, 7:20, 8:19,9:20, 10:21,11:22,  12:23,  13:24,  14:25,  15:26,  16:None},
                                                              12:{0:None,1:34,  2:33,  3:32,  4:31,  5:30,  6:29, 7:28, 8:27,9:28, 10:29,11:30,  12:31,  13:32,  14:33,  15:34,  16:None},
                                                              13:{0:None,1:None,2:41,  3:40,  4:39,  5:38,  6:37, 7:36, 8:35,9:36, 10:37,11:38,  12:39,  13:40,  14:41,  15:None,16:None},
                                                              14:{0:None,1:None,2:None,3:47,  4:46,  5:45,  6:44, 7:43, 8:42,9:43, 10:44,11:45,  12:46,  13:47,  14:None,15:None,16:None},
                                                              15:{0:None,1:None,2:None,3:None,4:52,  5:51,  6:50, 7:49, 8:48,9:49, 10:50,11:51,  12:52,  13:None,14:None,15:None,16:None},
                                                              16:{0:None,1:None,2:None,3:None,4:None,5:None,6:55, 7:54, 8:53,9:54, 10:55,11:None,12:None,13:None,14:None,15:None,16:None}}
CORE_MAPS['FULL']['QUARTER_MIRROR'][157]['WITHOUT_REFLECTOR'] = {0:{0:None, 1:None,  2:None,  3:None,  4:None,5:None, 6:39, 7:38, 8:39, 9:None,10:None,11:None,12:None,13:None,14:None},
                                                                 1:{0:None, 1:None,  2:None,  3:None,  4:37,  5:36,   6:35, 7:34, 8:35, 9:36,  10:37,  11:None,12:None,13:None,14:None},
                                                                 2:{0:None, 1:None,  2:None,  3:33,    4:32,  5:31,   6:30, 7:29, 8:30, 9:31,  10:32,  11:33,  12:None,13:None,14:None},
                                                                 3:{0:None, 1:None,  2:28,    3:27,    4:26,  5:25,   6:24, 7:23, 8:24, 9:25,  10:26,  11:27,  12:28,  13:None,14:None},
                                                                 4:{0:None, 1:22,    2:21,    3:20,    4:19,  5:18,   6:17, 7:16, 8:17, 9:18,  10:19,  11:20,  12:21,  13:22,  14:None},
                                                                 5:{0:None, 1:15,    2:14,    3:13,    4:12,  5:11,   6:10, 7:9,  8:10, 9:11,  10:12,  11:13,  12:14,  13:15,  14:None},
                                                                 6:{0:8,    1:7,     2:6,     3:5,     4:4,   5:3,    6:2,  7:1,  8: 2, 9: 3,  10: 4,  11:5,   12:6,   13:7,   14:8},
                                                                 7:{0:38,   1:34,    2:29,    3:23,    4:16,  5:9,    6:1,  7:0,  8: 1, 9: 9,  10:16,  11:23,  12:29,  13:34,  14:38},
                                                                 8:{0:8,    1:7,     2:6,     3:5,     4:4,   5:3,    6:2,  7:1,  8: 2, 9: 3,  10: 4,  11:5,   12:6,   13:7,   14:8},                                                          
                                                                 9:{0:None, 1:15,    2:14,    3:13,    4:12,  5:11,   6:10, 7:9,  8:10, 9:11,  10:12,  11:13,  12:14,  13:15,  14:None},
                                                                10:{0:None, 1:22,    2:21,    3:20,    4:19,  5:18,   6:17, 7:16, 8:17, 9:18,  10:19,  11:20,  12:21,  13:22,  14:None},
                                                                11:{0:None, 1:None,  2:28,    3:27,    4:26,  5:25,   6:24, 7:23, 8:24, 9:25,  10:26,  11:27,  12:28,  13:None,14:None},
                                                                12:{0:None, 1:None,  2:None,  3:33,    4:32,  5:31,   6:30, 7:29, 8:30, 9:31,  10:32,  11:33,  12:None,13:None,14:None},
                                                                13:{0:None, 1:None,  2:None,  3:None,  4:37,  5:36,   6:35, 7:34, 8:35, 9:36,  10:37,  11:None,12:None,13:None,14:None},
                                                                14:{0:None, 1:None,  2:None,  3:None,  4:None,5:None, 6:39, 7:38, 8:39, 9:None,10:None,11:None,12:None,13:None,14:None}} 
CORE_MAPS['FULL']['QUARTER_MIRROR'][193] = {}
CORE_MAPS['FULL']['QUARTER_MIRROR'][193]['WITH_REFLECTOR'] = {}
CORE_MAPS['FULL']['QUARTER_MIRROR'][193]['WITHOUT_REFLECTOR'] = {0:{0:None,1:None,2:None,3:None,4:46,5:45,6:44,  7:43,  8:44,9:45, 10:46,11:None,12:None,13:None,14:None},
                                                                 1:{0:None,1:None,2:None,3:42,  4:41,5:40,6:39,  7:38,  8:39,9:40, 10:41,11:42,  12:None,13:None,14:None},
                                                                 2:{0:None,1:None,2:37,  3:36,  4:35,5:34,6:33,  7:32,  8:33,9:34, 10:35,11:36,  12:37,  13:None,14:None},
                                                                 3:{0:None,1:31,  2:30,  3:29,  4:28,5:27,6:26,  7:25,  8:26,9:27, 10:28,11:29,  12:30,  13:31,  14:None},
                                                                 4:{0:24,  1:23,  2:22,  3:21,  4:20,5:19,6:18,  7:17,  8:18,9:19, 10:20,11:21,  12:22,  13:23,  14:24},
                                                                 5:{0:16,  1:15,  2:14,  3:13,  4:12,5:11,6:10,  7:9,   8:10,9:11, 10:12,11:13,  12:14,  13:15,  14:16},
                                                                 6:{0:8,   1:7,   2:6,   3:5,   4:4, 5:3, 6:2,   7:1,   8:2, 9:3,  10:4, 11:5,   12:6,   13:7,   14:8},
                                                                 7:{0:43,  1:38,  2:32,  3:25,  4:17,5:9, 6:1,   7:0,   8:1, 9:9,  10:17,11:25,  12:32,  13:38,  14:43},
                                                                 8:{0:8,   1:7,   2:6,   3:5,   4:4, 5:3, 6:2,   7:1,   8:2, 9:3,  10:4, 11:5,   12:6,   13:7,   14:8},
                                                                 9:{0:16,  1:15,  2:14,  3:13,  4:12,5:11,6:10,  7:9,   8:10,9:11, 10:12,11:13,  12:14,  13:15,  14:16},
                                                                10:{0:24,  1:23,  2:22,  3:21,  4:20,5:19,6:18,  7:17,  8:18,9:19, 10:20,11:21,  12:22,  13:23,  14:24},
                                                                11:{0:None,1:31,  2:30,  3:29,  4:28,5:27,6:26,  7:25,  8:26,9:27, 10:28,11:29,  12:30,  13:31,  14:None},
                                                                12:{0:None,1:None,2:37,  3:36,  4:35,5:34,6:33,  7:32,  8:33,9:34, 10:35,11:36,  12:37,  13:None,14:None},
                                                                13:{0:None,1:None,2:None,3:42,  4:41,5:40,6:39,  7:38,  8:39,9:40, 10:41,11:42,  12:None,13:None,14:None},
                                                                14:{0:None,1:None,2:None,3:None,4:46,5:45,6:44,  7:43,  8:44,9:45, 10:46,11:None,12:None,13:None,14:None}}

CORE_MAPS['FULL']['QUARTER_MIRROR'][241] = {}
CORE_MAPS['FULL']['QUARTER_MIRROR'][241]['WITH_REFLECTOR'] = {0:{0:None,1:None,2:None,3:None,4:None,5:78, 6:77, 7:76, 8:75, 9:74, 10:75, 11:76, 12:77, 13:78, 14:None,15:None,16:None,17:None,18:None},                      
                                                              1:{ 0:None,1:None,2:None,3:73,  4:72,  5:71, 6:70, 7:69, 8:68, 9:67, 10:68, 11:69, 12:70, 13:71, 14:72,  15:73,  16:None,17:None,18:None},                            
                                                              2:{ 0:None,1:None,2:66,  3:65,  4:64,  5:63, 6:62, 7:61, 8:60, 9:59, 10:60, 11:61, 12:62, 13:63, 14:64,  15:65,  16:66,  17:None,18:None},          
                                                              3:{ 0:None,1:58,  2:57,  3:56,  4:55,  5:54, 6:53, 7:52, 8:51, 9:50, 10:51, 11:52, 12:53, 13:54, 14:55,  15:56,  16:57,  17:58,  18:None},          
                                                              4:{ 0:None,1:49,  2:48,  3:47,  4:46,  5:45, 6:44, 7:43, 8:42, 9:41, 10:42, 11:43, 12:44, 13:45, 14:46,  15:47,  16:48,  17:49,  18:None},
                                                              5:{ 0:40,  1:39,  2:38,  3:37,  4:36,  5:35, 6:34, 7:33, 8:32, 9:31, 10:32, 11:33, 12:34, 13:35, 14:36,  15:37,  16:38,  17:39,  18:40},
                                                              6:{ 0:30,  1:29,  2:28,  3:27,  4:26,  5:25, 6:24, 7:23, 8:22, 9:21, 10:22, 11:23, 12:24, 13:25, 14:26,  15:27,  16:28,  17:29,  18:30},
                                                              7:{ 0:20,  1:19,  2:18,  3:17,  4:16,  5:15, 6:14, 7:13, 8:12, 9:11, 10:12, 11:13, 12:14, 13:15, 14:16,  15:17,  16:18,  17:19,  18:20},
                                                              8:{ 0:10,  1: 9,  2: 8,  3: 7,  4: 6,  5: 5, 6: 4, 7: 3, 8: 2, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6,  15: 7,  16: 8,  17: 9,  18:10},         
                                                              9:{ 0:74,  1:67,  2:59,  3:50,  4:41,  5:31, 6:21, 7:11, 8: 1, 9: 0, 10: 1, 11:11, 12:21, 13:31, 14:41,  15:50,  16:59,  17:67,  18:74},
                                                             10:{ 0:10,  1: 9,  2: 8,  3: 7,  4: 6,  5: 5, 6: 4, 7: 3, 8: 2, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6,  15: 7,  16: 8,  17: 9,  18:10},
                                                             11:{ 0:20,  1:19,  2:18,  3:17,  4:16,  5:15, 6:14, 7:13, 8:12, 9:11, 10:12, 11:13, 12:14, 13:15, 14:16,  15:17,  16:18,  17:19,  18:20},
                                                             12:{ 0:30,  1:29,  2:28,  3:27,  4:26,  5:25, 6:24, 7:23, 8:22, 9:21, 10:22, 11:23, 12:24, 13:25, 14:26,  15:27,  16:28,  17:29,  18:30},
                                                             13:{ 0:40,  1:39,  2:38,  3:37,  4:36,  5:35, 6:34, 7:33, 8:32, 9:31, 10:32, 11:33, 12:34, 13:35, 14:36,  15:37,  16:38,  17:39,  18:40},
                                                             14:{ 0:None,1:49,  2:48,  3:47,  4:46,  5:45, 6:44, 7:43, 8:42, 9:41, 10:42, 11:43, 12:44, 13:45, 14:46,  15:47,  16:48,  17:49,  18:None},         
                                                             15:{ 0:None,1:58,  2:57,  3:56,  4:55,  5:54, 6:53, 7:52, 8:51, 9:50, 10:51, 11:52, 12:53, 13:54, 14:55,  15:56,  16:57,  17:58,  18:None},         
                                                             16:{ 0:None,1:None,2:66,  3:65,  4:64,  5:63, 6:62, 7:61, 8:60, 9:59, 10:60, 11:61, 12:62, 13:63, 14:64,  15:65,  16:66,  17:None,18:None},         
                                                             17:{ 0:None,1:None,2:None,3:73,  4:72,  5:71, 6:70, 7:69, 8:68, 9:67, 10:68, 11:69, 12:70, 13:71, 14:72,  15:73,  16:None,17:None,18:None},                     
                                                             18:{ 0:None,1:None,2:None,3:None,4:None,5:78, 6:77, 7:76, 8:75, 9:74, 10:75, 11:76, 12:77, 13:78, 14:None,15:None,16:None,17:None,18:None}}
CORE_MAPS['FULL']['QUARTER_MIRROR'][241]['WITHOUT_REFLECTOR'] = {0:{0:None,1:None,2:None,3:None,4:None,5:60, 6:59, 7:58, 8:57, 9:58, 10:59, 11:60, 12:None, 13:None, 14:None, 15:None, 16:None},                
                                                                 1:{0:None,1:None,2:None,3:56,  4:55,  5:54, 6:53, 7:52, 8:51, 9:52, 10:53, 11:54, 12:55,   13:56,   14:None, 15:None, 16:None},        
                                                                 2:{0:None,1:None,2:50,  3:49,  4:48,  5:47, 6:46, 7:45, 8:44, 9:45, 10:46, 11:47, 12:48,   13:49,   14:50,   15:None, 16:None},        
                                                                 3:{0:None,1:43,  2:42,  3:41,  4:40,  5:39, 6:38, 7:37, 8:36, 9:37, 10:38, 11:39, 12:40,   13:41,   14:42,   15:43,   16:None},    
                                                                 4:{0:None,1:35,  2:34,  3:33,  4:32,  5:31, 6:30, 7:29, 8:28, 9:29, 10:30, 11:31, 12:32,   13:33,   14:34,   15:35,   16:None},    
                                                                 5:{0:27,  1:26,  2:25,  3:24,  4:23,  5:22, 6:21, 7:20, 8:19, 9:20, 10:21, 11:22, 12:23,   13:24,   14:25,   15:26,   16:27  }, 
                                                                 6:{0:18,  1:17,  2:16,  3:15,  4:14,  5:13, 6:12, 7:11, 8:10, 9:11, 10:12, 11:13, 12:14,   13:15,   14:16,   15:17,   16:18  },  
                                                                 7:{0: 9,  1: 8,  2: 7,  3: 6,  4: 5,  5: 4, 6: 3, 7: 2, 8: 1, 9: 2, 10: 3, 11: 4, 12: 5,   13: 6,   14: 7,   15: 8,   16: 9  },    
                                                                 8:{0:57,  1:51,  2:44,  3:36,  4:28,  5:19, 6:10, 7: 1, 8: 0, 9: 1, 10:10, 11:19, 12:28,   13:36,   14:44,   15:51,   16:57  },   
                                                                 9:{0: 9,  1: 8,  2: 7,  3: 6,  4: 5,  5: 4, 6: 3, 7: 2, 8: 1, 9: 2, 10: 3, 11: 4, 12: 5,   13: 6,   14: 7,   15: 8,   16: 9  },    
                                                                10:{0:18,  1:17,  2:16,  3:15,  4:14,  5:13, 6:12, 7:11, 8:10, 9:11, 10:12, 11:13, 12:14,   13:15,   14:16,   15:17,   16:18  }, 
                                                                11:{0:27,  1:26,  2:25,  3:24,  4:23,  5:22, 6:21, 7:20, 8:19, 9:20, 10:21, 11:22, 12:23,   13:24,   14:25,   15:26,   16:27  }, 
                                                                12:{0:None,1:35,  2:34,  3:33,  4:32,  5:31, 6:30, 7:29, 8:28, 9:29, 10:30, 11:31, 12:32,   13:33,   14:34,   15:35,   16:None},  
                                                                13:{0:None,1:43,  2:42,  3:41,  4:40,  5:39, 6:38, 7:37, 8:36, 9:37, 10:38, 11:39, 12:40,   13:41,   14:42,   15:43,   16:None},    
                                                                14:{0:None,1:None,2:50,  3:49,  4:48,  5:47, 6:46, 7:45, 8:44, 9:45, 10:46, 11:47, 12:48,   13:49,   14:50,   15:None, 16:None},        
                                                                15:{0:None,1:None,2:None,3:56,  4:55,  5:54, 6:53, 7:52, 8:51, 9:52, 10:53, 11:54, 12:55,   13:56,   14:None, 15:None, 16:None},        
                                                                16:{0:None,1:None,2:None,3:None,4:None,5:60, 6:59, 7:58, 8:57, 9:58, 10:59, 11:60, 12:None, 13:None, 14:None, 15:None, 16:None}}                              
CORE_MAPS['FULL']['QUARTER_ROTATIONAL'] = {}
CORE_MAPS['FULL']['QUARTER_ROTATIONAL'][157] = {}
CORE_MAPS['FULL']['QUARTER_ROTATIONAL'][157]['WITH_REFLECTOR'] = {0:{0:None,1:None,2:None,3:None,4:None,5:None,6:55, 7:54,8:53,9:9, 10:18,11:None,12:None,13:None,14:None,15:None,16:None},
                                                                  1:{0:None,1:None,2:None,3:None,4:52,  5:51,  6:50, 7:49,8:48,9:8, 10:17,11:26,  12:34,  13:None,14:None,15:None,16:None},
                                                                  2:{0:None,1:None,2:None,3:47,  4:46,  5:45,  6:44, 7:43,8:42,9:7, 10:16,11:25,  12:33,  13:41,  14:None,15:None,16:None},
                                                                  3:{0:None,1:None,2:41,  3:40,  4:39,  5:38,  6:37, 7:36,8:35,9:6, 10:15,11:24,  12:32,  13:40,  14:47,  15:None,16:None},
                                                                  4:{0:None,1:34,  2:33,  3:32,  4:31,  5:30,  6:29, 7:28,8:27,9:5, 10:14,11:23,  12:31,  13:39,  14:46,  15:52,  16:None},
                                                                  5:{0:None,1:26,  2:25,  3:24,  4:23,  5:22,  6:21, 7:20,8:19,9:4, 10:13,11:22,  12:30,  13:38,  14:45,  15:51,  16:None},
                                                                  6:{0:18,  1:17,  2:16,  3:15,  4:14,  5:13,  6:12, 7:11,8:10,9:3, 10:12,11:21,  12:29,  13:37,  14:44,  15:50,  16:55},
                                                                  7:{0:9,   1:8,   2:7,   3:6,   4:5,   5:4,   6:3,  7:2, 8:1, 9:2, 10:11,11:20,  12:28,  13:36,  14:43,  15:49,  16:54},
                                                                  8:{0:53,  1:48,  2:42,  3:35,  4:27,  5:19,  6:10, 7:1, 8:0, 9:1, 10:10,11:19,  12:27,  13:35,  14:42,  15:48,  16:53},
                                                                  9:{0:54,  1:49,  2:43,  3:36,  4:28,  5:20,  6:11, 7:2, 8:1, 9:2, 10:3, 11:4,   12:5,   13:6,   14:7,   15:8,   16:9},
                                                                 10:{0:55,  1:50,  2:44,  3:37,  4:29,  5:21,  6:12, 7:3, 8:10,9:11,10:12,11:13,  12:14,  13:15,  14:16,  15:17,  16:18},
                                                                 11:{0:None,1:51,  2:45,  3:38,  4:30,  5:22,  6:13, 7:4, 8:19,9:20,10:21,11:22,  12:23,  13:24,  14:25,  15:26,  16:None},
                                                                 12:{0:None,1:52,  2:46,  3:39,  4:31,  5:23,  6:14, 7:5, 8:27,9:28,10:29,11:30,  12:31,  13:32,  14:33,  15:34,  16:None},
                                                                 13:{0:None,1:None,2:47,  3:40,  4:32,  5:24,  6:15, 7:6, 8:35,9:36,10:37,11:38,  12:39,  13:40,  14:41,  15:None,16:None},
                                                                 14:{0:None,1:None,2:None,3:41,  4:33,  5:25,  6:16, 7:7, 8:42,9:43,10:44,11:45,  12:46,  13:47,  14:None,15:None,16:None},
                                                                 15:{0:None,1:None,2:None,3:None,4:34,  5:26,  6:17, 7:8, 8:48,9:49,10:50,11:51,  12:52,  13:None,14:None,15:None,16:None},
                                                                 16:{0:None,1:None,2:None,3:None,4:None,5:None,6:18, 7:9, 8:53,9:54,10:55,11:None,12:None,13:None,14:None,15:None,16:None}}
CORE_MAPS['FULL']['QUARTER_ROTATIONAL'][157]['WITHOUT_REFLECTOR'] = {0 :{0:None, 1:None,  2:None,  3:None,  4:None,  5:None,  6:39,  7:38,  8: 8,  9:None,  10:None  , 11:None, 12:None, 13:None, 14:None},
                                                                     1 :{0:None, 1:None,  2:None,  3:None,  4:37,    5:36,    6:35,  7:34,  8: 7,  9:15,    10:22,     11:None, 12:None, 13:None, 14:None},
                                                                     2 :{0:None, 1:None,  2:None,  3:33,    4:32,    5:31,    6:30,  7:29,  8: 6,  9:14,    10:21,     11:28,   12:None, 13:None, 14:None},
                                                                     3 :{0:None, 1:None,  2:28,    3:27,    4:26,    5:25,    6:24,  7:23,  8: 5,  9:13,    10:20,     11:27,   12:33,   13:None, 14:None},
                                                                     4 :{0:None, 1:22,    2:21,    3:20,    4:19,    5:18,    6:17,  7:16,  8: 4,  9:12,    10:19,     11:26,   12:32,   13:37,   14:None},
                                                                     5 :{0:None, 1:15,    2:14,    3:13,    4:12,    5:11,    6:10,  7: 9,  8: 3,  9:11,    10:18,     11:25,   12:31,   13:36,   14:None},
                                                                     6 :{0: 8,   1: 7,    2: 6,    3: 5,    4: 4,    5: 3,    6:2,   7: 1,  8: 2,  9:10,    10:17,     11:24,   12:30,   13:35,   14:39},
                                                                     7 :{0:38,   1:34,    2:29,    3:23,    4:16,    5: 9,    6:1,   7: 0,  8: 1,  9: 9,    10:16,     11:23,   12:29,   13:34,   14:38},
                                                                     8 :{0:39,   1:35,    2:30,    3:24,    4:17,    5:10,    6:2,   7: 1,  8: 2,  9: 3,    10: 4,     11: 5,   12: 6,   13: 7,   14: 8},                                                           
                                                                     9 :{0:None, 1:36,    2:31,    3:25,    4:18,    5:11,    6:4,   7:3,   8:4,   9:5,     10:8,      11:12,   12:17,   13:22,   14:None},
                                                                     10:{0:None, 1:37,    2:32,    3:26,    4:19,    5:12,    6:4,   7:16,  8:17,  9:18,    10:19,     11:20,   12:21,   13:22,   14:None},
                                                                     11:{0:None, 1:None,  2:33,    3:27,    4:20,    5:13,    6:5,   7:23,  8:24,  9:25,    10:26,     11:27,   12:28,   13:None, 14:None},
                                                                     12:{0:None, 1:None,  2:None,  3:28,    4:21,    5:14,    6:6,   7:29,  8:30,  9:31,    10:32,     11:33,   12:None, 13:None, 14:None},
                                                                     13:{0:None, 1:None,  2:None,  3:None,  4:22,    5:15,    6:7,   7:34,  8:35,  9:36,    10:37,     11:None, 12:None, 13:None, 14:None},
                                                                     14:{0:None, 1:None,  2:None,  3:None,  4:None,  5:None,  6:8,   7:38,  8:39,  9:None,  10:None  , 11:None, 12:None, 13:None, 14:None}} 
CORE_MAPS['FULL']['QUARTER_ROTATIONAL'][193] = {}

CORE_MAPS['FULL']['QUARTER_ROTATIONAL'][193]['WITH_REFLECTOR'] = {0:{0:None,1:None,2:None,3:None,4:None,5:78,6:77,7:76,8:75,9:74,10:75,11:76,12:77,13:78,14:None,15:None,16:None,17:None,18:None},
                                                                  1:{0:None,1:None,2:None,3:73,  4:72,  5:71,6:70,7:69,8:68,9:67,10:68,11:69,12:70,13:71,14:72,  15:73,  16:None,17:None,18:None},
                                                                  2:{0:None,1:None,2:66,  3:65,  4:64,  5:63,6:62,7:61,8:8, 9:59,10:8, 11:61,12:62,13:63,14:64,  15:65,  16:66,  17:None,18:None},
                                                                  3:{0:None,1:58,  2:57,  3:56,  4:55,  5:54,6:53,7:52,8:51,9:50,10:51,11:52,12:53,13:54,14:55,  15:56,  16:57,  17:58,  18:None},
                                                                  4:{0:None,1:49,  2:48,  3:47,  4:46,  5:45,6:44,7:43,8:42,9:41,10:42,11:43,12:44,13:45,14:46,  15:47,  16:48,  17:49,  18:None},
                                                                  5:{0:40,  1:39,  2:38,  3:37,  4:36,  5:35,6:34,7:33,8:32,9:31,10:32,11:33,12:34,13:35,14:36,  15:37,  16:38,  17:39,  18:40  },
                                                                  6:{0:30,  1:29,  2:28,  3:27,  4:26,  5:25,6:24,7:23,8:22,9:21,10:22,11:23,12:24,13:25,14:26,  15:27,  16:28,  17:29,  18:30  },
                                                                  7:{0:20,  1:19,  2:18,  3:17,  4:16,  5:15,6:14,7:13,8:12,9:11,10:12,11:13,12:14,13:15,14:16,  15:17,  16:18,  17:19,  18:20  },
                                                                  8:{0:10,  1:9 ,  2:8 ,  3:7,   4:6 ,  5:5 ,6:4 ,7:3, 8:2 ,9:1, 10:2 ,11:3 ,12:4 ,13:5 ,14:6 ,  15:7 ,  16:8 ,  17:9 ,  18:10  },
                                                                  9:{0:74,  1:67,  2:59,  3:50,  4:41,  5:31,6:21,7:11,8:1 ,9:0, 10:1 ,11:11,12:21,13:31,14:41,  15:50,  16:59,  17:67,  18:74  },
                                                                 10:{0:10,  1:9 ,  2:8 ,  3:51,  4:6 ,  5:5 ,6:4 ,7:3 ,8:2 ,9:1, 10:2 ,11:3 ,12:4 ,13:5 ,14:6 ,  15:7 ,  16:8 ,  17:9 ,  18:10  },
                                                                 11:{0:20,  1:19,  2:18,  3:52,  4:16,  5:15,6:14,7:13,8:12,9:11,10:12,11:13,12:14,13:15,14:16,  15:17,  16:18,  17:19,  18:20  },
                                                                 12:{0:30,  1:29,  2:28,  3:53,  4:26,  5:25,6:24,7:23,8:22,9:21,10:22,11:23,12:24,13:25,14:26,  15:27,  16:28,  17:29,  18:30  },
                                                                 13:{0:40,  1:39,  2:38,  3:54,  4:36,  5:35,6:34,7:33,8:32,9:31,10:32,11:33,12:34,13:35,14:36,  15:37,  16:38,  17:39,  18:40  },
                                                                 14:{0:None,1:49,  2:48,  3:55,  4:46,  5:45,6:44,7:43,8:42,9:41,10:42,11:43,12:44,13:45,14:46,  15:47,  16:48,  17:49,  18:None},
                                                                 15:{0:None,1:58,  2:57,  3:56,  4:55,  5:54,6:53,7:52,8:51,9:50,10:51,11:52,12:53,13:54,14:55,  15:56,  16:57,  17:58,  18:None},
                                                                 16:{0:None,1:None,2:66,  3:57,  4:64,  5:63,6:62,7:61,8:60,9:59,10:60,11:61,12:62,13:63,14:64,  15:65,  16:66,  17:None,18:None},
                                                                 17:{0:None,1:None,2:None,3:58,  4:72,  5:71,6:70,7:69,8:68,9:67,10:68,11:69,12:70,13:71,14:72,  15:73,  16:None,17:None,18:None},
                                                                 18:{0:None,1:None,2:None,3:None,4:None,5:78,6:77,7:76,8:75,9:74,10:75,11:76,12:77,13:78,14:None,15:None,16:None,17:None,18:None}}

CORE_MAPS['FULL']['QUARTER_ROTATIONAL'][193]['WITHOUT_REFLECTOR'] = {0:{0:None,1:None,2:None,3:None,4:48,  5:47, 6:46, 7:45, 8:8,  9:16,  10:24, 11:None,12:None,13:None,14:None},
                                                                     1:{0:None,1:None,2:44,  3:43,  4:42,  5:41, 6:40, 7:39, 8:7,  9:15,  10:23, 11:31,  12:38,  13:None,14:None},
                                                                     2:{0:None,1:38,  2:37,  3:36,  4:35,  5:34, 6:33, 7:32, 8:6,  9:14,  10:22, 11:30,  12:37,  13:44,  14:None},
                                                                     3:{0:None,1:31,  2:30,  3:29,  4:28,  5:27, 6:26, 7:25, 8:5,  9:13,  10:21, 11:29,  12:36,  13:43,  14:None},
                                                                     4:{0:24,  1:23,  2:22,  3:21,  4:20,  5:19, 6:18, 7:17, 8:4,  9:12,  10:20, 11:28,  12:35,  13:42,  14:48},
                                                                     5:{0:16,  1:15,  2:14,  3:13,  4:12,  5:11, 6:10, 7:9,  8:3,  9:11,  10:19, 11:27,  12:34,  13:41,  14:47},
                                                                     6:{0:8,   1:7,   2:6,   3:5,   4:4,   5:3,  6:2,  7:1,  8:2,  9:10,  10:18, 11:26,  12:33,  13:40,  14:46},
                                                                     7:{0:45,  1:39,  2:32,  3:25,  4:17,  5:9,  6:1,  7:0,  8:1,  9:9,   10:17, 11:25,  12:32,  13:39,  14:45},
                                                                     8:{0:46,  1:40,  2:33,  3:26,  4:18,  5:10, 6:2,  7:1,  8:2,  9:3,   10:4,  11:5,   12:6,   13:7,   14:8},
                                                                     9:{0:47,  1:41,  2:34,  3:27,  4:19,  5:11, 6:3,  7:9,  8:10, 9:11,  10:12, 11:13,  12:14,  13:15,  14:16},
                                                                    10:{0:48,  1:42,  2:35,  3:28,  4:20,  5:12, 6:4,  7:17, 8:18, 9:19,  10:20, 11:21,  12:22,  13:23,  14:24},
                                                                    11:{0:None,1:43,  2:36,  3:29,  4:21,  5:13, 6:5,  7:25, 8:26, 9:27,  10:28, 11:29,  12:30,  13:31,  14:None},
                                                                    12:{0:None,1:44,  2:37,  3:30,  4:22,  5:14, 6:6,  7:32, 8:33, 9:34,  10:35, 11:36,  12:37,  13:38,  14:None},
                                                                    13:{0:None,1:None,2:38,  3:31,  4:23,  5:15, 6:7,  7:39, 8:40, 9:41,  10:42, 11:43,  12:44,  13:None,14:None},
                                                                    14:{0:None,1:None,2:None,3:None,4:24,  5:16, 6:8,  7:45, 8:46, 9:47,  10:48, 11:None,12:None,13:None,14:None}}

CORE_MAPS['FULL']['QUARTER_ROTATIONAL'][241] = {}
CORE_MAPS['FULL']['QUARTER_ROTATIONAL'][241]['WITH_REFLECTOR'] = {0:{ 0:None,1:None,2:None,3:None,4:None,5:78, 6:77, 7:76, 8:75, 9:74, 10:10, 11:20, 12:30, 13:40, 14:None,15:None,16:None,17:None,18:None},                      
                                                                  1:{ 0:None,1:None,2:None,3:73,  4:72,  5:71, 6:70, 7:69, 8:68, 9:67, 10: 9, 11:19, 12:29, 13:39, 14:49,  15:58,  16:None,17:None,18:None},                            
                                                                  2:{ 0:None,1:None,2:66,  3:65,  4:64,  5:63, 6:62, 7:61, 8:60, 9:59, 10: 8, 11:18, 12:28, 13:38, 14:48,  15:57,  16:66,  17:None,18:None},          
                                                                  3:{ 0:None,1:58,  2:57,  3:56,  4:55,  5:54, 6:53, 7:52, 8:51, 9:50, 10: 7, 11:17, 12:27, 13:37, 14:47,  15:56,  16:65,  17:73,  18:None},          
                                                                  4:{ 0:None,1:49,  2:48,  3:47,  4:46,  5:45, 6:44, 7:43, 8:42, 9:41, 10: 6, 11:16, 12:26, 13:36, 14:46,  15:55,  16:64,  17:72,  18:None},
                                                                  5:{ 0:40,  1:39,  2:38,  3:37,  4:36,  5:35, 6:34, 7:33, 8:32, 9:31, 10: 5, 11:15, 12:25, 13:35, 14:45,  15:54,  16:63,  17:71,  18:78},
                                                                  6:{ 0:30,  1:29,  2:28,  3:27,  4:26,  5:25, 6:24, 7:23, 8:22, 9:21, 10: 4, 11:14, 12:24, 13:34, 14:44,  15:53,  16:62,  17:70,  18:77},
                                                                  7:{ 0:20,  1:19,  2:18,  3:17,  4:16,  5:15, 6:14, 7:13, 8:12, 9:11, 10: 3, 11:13, 12:23, 13:33, 14:43,  15:52,  16:61,  17:69,  18:76},
                                                                  8:{ 0:10,  1: 9,  2: 8,  3: 7,  4: 6,  5: 5, 6: 4, 7: 3, 8: 2, 9: 1, 10: 2, 11:12, 12:22, 13:32, 14:42,  15:51,  16:60,  17:68,  18:75},         
                                                                  9:{ 0:74,  1:67,  2:59,  3:50,  4:41,  5:31, 6:21, 7:11, 8: 1, 9: 0, 10: 1, 11:11, 12:21, 13:31, 14:41,  15:50,  16:59,  17:67,  18:74},
                                                                 10:{ 0:75,  1:68,  2:60,  3:51,  4:42,  5:32, 6:22, 7:12, 8: 2, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6,  15: 7,  16: 8,  17: 9,  18:10},
                                                                 11:{ 0:76,  1:69,  2:61,  3:52,  4:43,  5:33, 6:23, 7:13, 8: 3, 9:11, 10:12, 11:13, 12:14, 13:15, 14:16,  15:17,  16:18,  17:19,  18:20},
                                                                 12:{ 0:77,  1:70,  2:62,  3:53,  4:44,  5:34, 6:24, 7:14, 8: 4, 9:21, 10:22, 11:23, 12:24, 13:25, 14:26,  15:27,  16:28,  17:29,  18:30},
                                                                 13:{ 0:78,  1:71,  2:63,  3:54,  4:45,  5:35, 6:25, 7:15, 8: 5, 9:31, 10:32, 11:33, 12:34, 13:35, 14:36,  15:37,  16:38,  17:39,  18:40},
                                                                 14:{ 0:None,1:72,  2:64,  3:55,  4:46,  5:36, 6:26, 7:16, 8: 6, 9:41, 10:42, 11:43, 12:44, 13:45, 14:46,  15:47,  16:48,  17:49,  18:None},         
                                                                 15:{ 0:None,1:73,  2:65,  3:56,  4:47,  5:37, 6:27, 7:17, 8: 7, 9:50, 10:51, 11:52, 12:53, 13:54, 14:55,  15:56,  16:57,  17:58,  18:None},         
                                                                 16:{ 0:None,1:None,2:66,  3:57,  4:48,  5:38, 6:28, 7:18, 8: 8, 9:59, 10:60, 11:61, 12:62, 13:63, 14:64,  15:65,  16:66,  17:None,18:None},         
                                                                 17:{ 0:None,1:None,2:None,3:58,  4:49,  5:39, 6:29, 7:19, 8: 9, 9:67, 10:68, 11:69, 12:70, 13:71, 14:72,  15:73,  16:None,17:None,18:None},                     
                                                                 18:{ 0:None,1:None,2:None,3:None,4:None,5:40, 6:30, 7:20, 8:10, 9:74, 10:75, 11:76, 12:77, 13:78, 14:None,15:None,16:None,17:None,18:None}}
CORE_MAPS['FULL']['QUARTER_ROTATIONAL'][241]['WITHOUT_REFLECTOR'] = {0:{0:None,1:None,2:None,3:None,4:None,5:60, 6:59, 7:58, 8:57, 9: 9, 10:18, 11:27, 12:None, 13:None, 14:None, 15:None, 16:None},                
                                                                     1:{0:None,1:None,2:None,3:56,  4:55,  5:54, 6:53, 7:52, 8:51, 9: 8, 10:17, 11:26, 12:35,   13:43,   14:None, 15:None, 16:None},        
                                                                     2:{0:None,1:None,2:50,  3:49,  4:48,  5:47, 6:46, 7:45, 8:44, 9: 7, 10:16, 11:25, 12:34,   13:42,   14:50,   15:None, 16:None},        
                                                                     3:{0:None,1:43,  2:42,  3:41,  4:40,  5:39, 6:38, 7:37, 8:36, 9: 6, 10:15, 11:24, 12:33,   13:41,   14:49,   15:56,   16:None},    
                                                                     4:{0:None,1:35,  2:34,  3:33,  4:32,  5:31, 6:30, 7:29, 8:28, 9: 5, 10:14, 11:23, 12:32,   13:40,   14:48,   15:55,   16:None},    
                                                                     5:{0:27,  1:26,  2:25,  3:24,  4:23,  5:22, 6:21, 7:20, 8:19, 9: 4, 10:13, 11:22, 12:31,   13:39,   14:47,   15:54,   16:60,  }, 
                                                                     6:{0:18,  1:17,  2:16,  3:15,  4:14,  5:13, 6:12, 7:11, 8:10, 9: 3, 10:12, 11:21, 12:30,   13:38,   14:46,   15:53,   16:59,  },  
                                                                     7:{0: 9,  1: 8,  2: 7,  3: 6,  4: 5,  5: 4, 6: 3, 7: 2, 8: 1, 9: 2, 10:11, 11:20, 12:29,   13:37,   14:45,   15:52,   16:58,  },    
                                                                     8:{0:57,  1:51,  2:44,  3:36,  4:28,  5:19, 6:10, 7: 1, 8: 0, 9: 1, 10:10, 11:19, 12:28,   13:36,   14:44,   15:51,   16:57,  },   
                                                                     9:{0:58,  1:52,  2:45,  3:37,  4:29,  5:20, 6:11, 7: 2, 8: 1, 9: 2, 10: 3, 11: 4, 12: 5,   13: 6,   14: 7,   15: 8,   16: 9,  },    
                                                                    10:{0:59,  1:53,  2:46,  3:38,  4:30,  5:21, 6:12, 7: 3, 8:10, 9:11, 10:12, 11:13, 12:14,   13:15,   14:16,   15:17,   16:18,  }, 
                                                                    11:{0:60,  1:54,  2:47,  3:39,  4:31,  5:22, 6:13, 7: 4, 8:19, 9:20, 10:21, 11:22, 12:23,   13:24,   14:25,   15:26,   16:27,  }, 
                                                                    12:{0:None,1:55,  2:48,  3:40,  4:32,  5:23, 6:14, 7: 5, 8:28, 9:29, 10:30, 11:31, 12:32,   13:33,   14:34,   15:35,   16:None},  
                                                                    13:{0:None,1:56,  2:49,  3:41,  4:33,  5:24, 6:15, 7: 6, 8:36, 9:37, 10:38, 11:39, 12:40,   13:41,   14:42,   15:43,   16:None},    
                                                                    14:{0:None,1:None,2:50,  3:42,  4:34,  5:25, 6:16, 7: 7, 8:44, 9:45, 10:46, 11:47, 12:48,   13:49,   14:50,   15:None, 16:None},        
                                                                    15:{0:None,1:None,2:None,3:43,  4:35,  5:26, 6:17, 7: 8, 8:51, 9:52, 10:53, 11:54, 12:55,   13:56,   14:None, 15:None, 16:None},        
                                                                    16:{0:None,1:None,2:None,3:None,4:None,5:27, 6:18, 7: 9, 8:57, 9:58, 10:59, 11:60, 12:None, 13:None, 14:None, 15:None, 16:None}}            
CORE_MAPS['QUARTER'] = {}        
CORE_MAPS['QUARTER']['QUARTER'] = {}
CORE_MAPS['QUARTER']['QUARTER'][157] = {}
CORE_MAPS['QUARTER']['QUARTER'][157]['WITH_REFLECTOR'] = {8:{8:0, 9:1,  10:10,11:19,  12:27,  13:35,  14:42,  15:48,  16:53},
                                                          9:{8:1, 9:2,  10:3, 11:4,   12:5,   13:6,   14:7,   15:8,   16:9},
                                                         10:{8:10,9:11, 10:12,11:13,  12:14,  13:15,  14:16,  15:17,  16:18},
                                                         11:{8:19,9:20, 10:21,11:22,  12:23,  13:24,  14:25,  15:26,  16:None},
                                                         12:{8:27,9:28, 10:29,11:30,  12:31,  13:32,  14:33,  15:34,  16:None},
                                                         13:{8:35,9:36, 10:37,11:38,  12:39,  13:40,  14:41,  15:None,16:None},
                                                         14:{8:42,9:43, 10:44,11:45,  12:46,  13:47,  14:None,15:None,16:None},
                                                         15:{8:48,9:49, 10:50,11:51,  12:52,  13:None,14:None,15:None,16:None},
                                                         16:{8:53,9:54, 10:55,11:None,12:None,13:None,14:None,15:None,16:None}}
CORE_MAPS['QUARTER']['QUARTER'][157]['WITHOUT_REFLECTOR'] = {7 :{7: 0,  8: 1,  9: 9,  10:16,  11:23, 12:29, 13:34, 14:38},
                                                             8 :{7: 1,  8: 2,  9: 3,  10: 4,  11: 5, 12: 6, 13: 7, 14: 8},                                                          
                                                             9 :{7: 9,  8:10,  9:11,  10:12,  11:13, 12:14, 13:15, 14:None},                                                          
                                                             10:{7:16,  8:17,  9:18,  10:19,  11:20, 12:21, 13:22, 14:None},                                                          
                                                             11:{7:23,  8:24,  9:25,  10:26,  11:27, 12:28,    13:None,14:None},                                                          
                                                             12:{7:29,  8:30,  9:31,  10:32,  11:33, 12:None,  13:None,14:None},                                                          
                                                             13:{7:34,  8:35,  9:36,  10:37,  11:None,12:None, 13:None,14:None},                                                          
                                                             14:{7:38,  8:39,  9:None,10:None,11:None,12:None, 13:None,14:None}}    
CORE_MAPS['QUARTER']['QUARTER'][193] = {}
CORE_MAPS['QUARTER']['QUARTER'][193]['WITH_REFLECTOR'] ={8:{8:0, 9:1, 10:10,11:19,12:28,13:37,  14:43,  15:51,  16:58},       #Edited input count
                                                         9:{8:1, 9:2, 10:3, 11:4, 12:5, 13:6,   14:7,   15:8,   16:9},
                                                        10:{8:10,9:11,10:12,11:13,12:14,13:15,  14:16,  15:17,  16:18},
                                                        11:{8:19,9:20,10:21,11:22,12:23,13:24,  14:25,  15:26,  16:27},
                                                        12:{8:28,9:29,10:30,11:31,12:32,13:33,  14:34,  15:35,  16:36},
                                                        13:{8:37,9:38,10:39,11:38,12:39,13:40,  14:41,  15:42,  16:None},
                                                        14:{8:43,9:44,10:45,11:46,12:47,13:48,  14:49,  15:50,  16:None},
                                                        15:{8:51,9:52,10:53,11:54,12:55,13:56,  14:57,  15:None,16:None},
                                                        16:{8:58,9:59,10:60,11:61,12:62,13:None,14:None,15:None,16:None}}
CORE_MAPS['QUARTER']['QUARTER'][193]['WITHOUT_REFLECTOR'] = {7 :{7:0,   8:1, 9:9,  10:17,11:25,  12:32,  13:38,  14:43},          
                                                             8 :{7:1,   8:2, 9:3,  10:4, 11:5,   12:6,   13:7,   14:8},
                                                             9 :{7:9,   8:10,9:11, 10:12,11:13,  12:14,  13:15,  14:16},
                                                             10:{7:17,  8:18,9:19, 10:20,11:21,  12:22,  13:23,  14:24},
                                                             11:{7:25,  8:26,9:27, 10:28,11:29,  12:30,  13:31,  14:None},
                                                             12:{7:32,  8:33,9:34, 10:35,11:36,  12:37,  13:None,14:None},
                                                             13:{7:38,  8:39,9:40, 10:41,11:42,  12:None,13:None,14:None},
                                                             14:{7:43,  8:44,9:45, 10:46,11:None,12:None,13:None,14:None}}
CORE_MAPS['QUARTER']['QUARTER'][241] = {}
CORE_MAPS['QUARTER']['QUARTER'][241]['WITH_REFLECTOR'] = {9:{9: 0, 10: 1, 11:11, 12:21, 13:31, 14:41,  15:50,  16:59,  17:67,  18:74},
                                                         10:{9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6,  15: 7,  16: 8,  17: 9,  18:10},
                                                         11:{9:11, 10:12, 11:13, 12:14, 13:15, 14:16,  15:17,  16:18,  17:19,  18:20},
                                                         12:{9:21, 10:22, 11:23, 12:24, 13:25, 14:26,  15:27,  16:28,  17:29,  18:30},
                                                         13:{9:31, 10:32, 11:33, 12:34, 13:35, 14:36,  15:37,  16:38,  17:39,  18:40},
                                                         14:{9:41, 10:42, 11:43, 12:44, 13:45, 14:46,  15:47,  16:48,  17:49,  18:None},         
                                                         15:{9:50, 10:51, 11:52, 12:53, 13:54, 14:55,  15:56,  16:57,  17:58,  18:None},         
                                                         16:{9:59, 10:60, 11:61, 12:62, 13:63, 14:64,  15:65,  16:66,  17:None,18:None},         
                                                         17:{9:67, 10:68, 11:69, 12:70, 13:71, 14:72,  15:73,  16:None,17:None,18:None},                     
                                                         18:{9:74, 10:75, 11:76, 12:77, 13:78, 14:None,15:None,16:None,17:None,18:None}}

CORE_MAPS['QUARTER']['QUARTER'][241]['WITHOUT_REFLECTOR'] = {8:{8: 0, 9: 1, 10:10, 11:19, 12:28,   13:36,   14:44,   15:51,   16:57  },   
                                                             9:{8: 1, 9: 2, 10: 3, 11: 4, 12: 5,   13: 6,   14: 7,   15: 8,   16: 9  },    
                                                            10:{8:10, 9:11, 10:12, 11:13, 12:14,   13:15,   14:16,   15:17,   16:18  }, 
                                                            11:{8:19, 9:20, 10:21, 11:22, 12:23,   13:24,   14:25,   15:26,   16:27  }, 
                                                            12:{8:28, 9:29, 10:30, 11:31, 12:32,   13:33,   14:34,   15:35,   16:None},  
                                                            13:{8:36, 9:37, 10:38, 11:39, 12:40,   13:41,   14:42,   15:43,   16:None},    
                                                            14:{8:44, 9:45, 10:46, 11:47, 12:48,   13:49,   14:50,   15:None, 16:None},        
                                                            15:{8:51, 9:52, 10:53, 11:54, 12:55,   13:56,   14:None, 15:None, 16:None},        
                                                            16:{8:57, 9:58, 10:59, 11:60, 12:None, 13:None, 14:None, 15:None, 16:None}}
CORE_MAPS['QUARTER']['OCTANT'] = {}
CORE_MAPS['QUARTER']['OCTANT'][157] = {}
CORE_MAPS['QUARTER']['OCTANT'][157]['WITH_REFLECTOR'] = {8:{8:0, 9:1, 10:3, 11:6,   12:10,  13:15,  14:21  , 15:27,  16:32},
                                                         9:{8:1, 9:2, 10:4, 11:7,   12:11,  13:16,  14:22  , 15:28,  16:33},
                                                        10:{8:3, 9:4, 10:5, 11:8,   12:12,  13:17,  14:23  , 15:29,  16:34},
                                                        11:{8:6, 9:7, 10:8, 11:9,   12:13,  13:18,  14:24  , 15:30,  16:None},
                                                        12:{8:10,9:11,10:12,11:13,  12:14,  13:19,  14:25  , 15:31,  16:None},
                                                        13:{8:15,9:16,10:17,11:18,  12:19,  13:20,  14:26  , 15:None,16:None},
                                                        14:{8:21,9:22,10:23,11:24,  12:25,  13:26,  14:None, 15:None,16:None},
                                                        15:{8:27,9:28,10:29,11:30,  12:31,  13:None,14:None, 15:None,16:None},
                                                        16:{8:32,9:33,10:34,11:None,12:None,13:None,14:None, 15:None,16:None}} 
CORE_MAPS['QUARTER']['OCTANT'][157]['WITHOUT_REFLECTOR'] = {7:{7:0,   8:1,  9:3,    10:6,    11:10,   12:15,   13:20,   14:24},
                                                            8:{7:1,   8:2,  9:4,    10:7,    11:11,   12:16,   13:21,   14:25},
                                                            9:{7:3,   8:4,  9:5,    10:8,    11:12,   12:17,   13:22,   14:None},
                                                            10:{7:6, 8:7,  9:8,    10:9,    11:13,   12:18,   13:23,   14:None},
                                                            11:{7:10, 8:11, 9:12,   10:13,   11:14,   12:19,   13:None, 14:None},
                                                            12:{7:15, 8:16, 9:17,   10:18,   11:19,   12:None, 13:None, 14:None},
                                                            13:{7:20, 8:21, 9:22,   10:23,   11:None, 12:None, 13:None, 14:None},
                                                            14:{7:24, 8:25, 9:None, 10:None, 11:None, 12:None, 13:None, 14:None}} 
CORE_MAPS['QUARTER']['OCTANT'][193] = {}
CORE_MAPS['QUARTER']['OCTANT'][193]['WITH_REFLECTOR'] = {8:{8:0, 9:1, 10:3, 11:6, 12:10,13:15,  14:21,  15:28,  16:35},       #Edited input count
                                                         9:{8:1, 9:2, 10:4, 11:7, 12:11,13:16,  14:22,  15:29,  16:36},
                                                        10:{8:3, 9:4, 10:5, 11:8, 12:12,13:17,  14:23,  15:30,  16:37},
                                                        11:{8:6, 9:7, 10:8, 11:9, 12:13,13:18,  14:24,  15:31,  16:38},
                                                        12:{8:10,9:11,10:12,11:13,12:14,13:19,  14:25,  15:32,  16:39},
                                                        13:{8:15,9:16,10:17,11:18,12:19,13:20,  14:26,  15:33,  16:None},
                                                        14:{8:21,9:22,10:23,11:24,12:25,13:26,  14:27,  15:34,  16:None},
                                                        15:{8:28,9:29,10:30,11:31,12:32,13:33,  14:34,  15:None,16:None},
                                                        16:{8:35,9:36,10:37,11:38,12:39,13:None,14:None,15:None,16:None}}
CORE_MAPS['QUARTER']['OCTANT'][193]['WITHOUT_REFLECTOR'] = {7:{7:0, 8:1, 9:3,  10:6, 11:10,  12:15,  13:21,  14:26},
                                                            8:{7:1, 8:2, 9:4,  10:7, 11:11,  12:16,  13:22,  14:27},
                                                            9:{7:3, 8:4, 9:5,  10:8, 11:12,  12:17,  13:23,  14:28},
                                                           10:{7:6, 8:7, 9:8,  10:9, 11:13,  12:18,  13:24,  14:29},
                                                           11:{7:10,8:11,9:12, 10:13,11:14,  12:19,  13:25,  14:None},
                                                           12:{7:15,8:16,9:17, 10:18,11:19,  12:20,  13:None,14:None},
                                                           13:{7:21,8:22,9:23, 10:24,11:25,  12:None,13:None,14:None},
                                                           14:{7:26,8:27,9:28, 10:29,11:None,12:None,13:None,14:None}}
CORE_MAPS['QUARTER']['OCTANT'][241] = {}
CORE_MAPS['QUARTER']['OCTANT'][241]['WITH_REFLECTOR'] = {9:{9: 0, 10: 1, 11: 3, 12: 6, 13:10, 14:15,  15:21,  16:28,  17:36,  18:43},
                                                        10:{9: 1, 10: 2, 11: 4, 12: 7, 13:11, 14:16,  15:22,  16:29,  17:37,  18:44},
                                                        11:{9: 3, 10: 4, 11: 5, 12: 8, 13:12, 14:17,  15:23,  16:30,  17:38,  18:45},
                                                        12:{9: 6, 10: 7, 11: 8, 12: 9, 13:13, 14:18,  15:24,  16:31,  17:39,  18:46},
                                                        13:{9:10, 10:11, 11:12, 12:13, 13:14, 14:19,  15:25,  16:32,  17:40,  18:47},
                                                        14:{9:15, 10:16, 11:17, 12:18, 13:19, 14:20,  15:26,  16:33,  17:41,  18:None},
                                                        15:{9:21, 10:22, 11:23, 12:24, 13:25, 14:26,  15:27,  16:34,  17:42,  18:None},
                                                        16:{9:28, 10:29, 11:30, 12:31, 13:32, 14:33,  15:34,  16:35,  17:None,18:None},
                                                        17:{9:36, 10:37, 11:38, 12:39, 13:40, 14:41,  15:42,  16:None,17:None,18:None},
                                                        18:{9:43, 10:44, 11:45, 12:46, 13:47, 14:None,15:None,16:None,17:None,18:None}}
CORE_MAPS['QUARTER']['OCTANT'][241]['WITHOUT_REFLECTOR'] = {8:{8:0,  9:1,  10:3,  11:6,  12:10,  13:15,  14:21,  15:28,  16:34  },
                                                            9:{8:1,  9:2,  10:4,  11:7,  12:11,  13:16,  14:22,  15:29,  16:35  },
                                                           10:{8:3,  9:4,  10:5,  11:8,  12:12,  13:17,  14:23,  15:30,  16:36  },
                                                           11:{8:6,  9:7,  10:8,  11:9,  12:13,  13:18,  14:24,  15:31,  16:37  },
                                                           12:{8:10, 9:11, 10:12, 11:13, 12:14,  13:19,  14:25,  15:32,  16:None},         
                                                           13:{8:15, 9:16, 10:17, 11:18, 12:19,  13:20,  14:26,  15:33,  16:None},     
                                                           14:{8:21, 9:22, 10:23, 11:24, 12:25,  13:26,  14:27,  15:None,16:None},     
                                                           15:{8:28, 9:29, 10:30, 11:31, 12:32,  13:33,  14:None,15:None,16:None},     
                                                           16:{8:34, 9:35, 10:36, 11:37, 12:None,13:None,14:None,15:None,16:None}}



                                                              
                                                                                 
    
