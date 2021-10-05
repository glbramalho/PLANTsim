# PLANTsim
PLANTsim: a digital twin framework in Python for industrial plants modeling and simulation

PLANTsim was developed to emulate the behaviour of an industrial process. It was
designed to create a digital twin of a didactic industrial process plant used to teach automation and
industrial networks concepts. PLANTsim can be used to demonstrate automation techniques and
develop industrial controller programming and supervisory control skills. This software was
developed in Python and is distributed as an open-source platform to teach industrial
automation concepts and techniques for engineering students.

Keywords: digital twin, industrial automation, process simulation

File-type:

.INI      PLANTsim configuration file. 
          [required]
          
.PLANT    Modeling file of the system to be simulated by PLANTsim. 
          [required] [PLANTsim model language]
          
.PRG      GRAFCET program file conaining steps, actions and transitions to control the 
          system model in .PLANT. 
          [optional] [GRAFCET language]

.SIM      File containing a pre-defined sequence of events that enables the states of the system 
          model in .PLANT. 
          [optional] [PLANTsim events language]

Features:

- MODBUS TCP comunication with PLCs (industrial controllers) and SCADA softwares (master or slave modes)
- Plant design and modeling using a high level text language (PLANTsim language)
- As an open framework it allows to create new devices and objects to expand and improve PLANTsim

Portuguese version ------------------------------------------------------------------------------

O PLANTsim foi desenvolvido para simular o comportamento de um processo industrial.
Ele foi projetado para criar um gêmeo digital de uma planta de processo industrial didático usada
para ensinar conceitos de automação e redes industriais. PLANTsim pode ser usado para
demonstrar técnicas de automação e desenvolver programação de controlador industrial e
habilidades de controle de supervisão. Este software foi desenvolvido em Python e é distribuído
como uma plataforma open-source para ensinar conceitos e técnicas de automação industrial para
estudantes de engenharia.

Palavras-chave: gêmeo digital, automação industrial, simulação de processo

Tipos de arquivo:

.INI      Arquivo de configuração do PLANTsim. 
          [necessário]

.PLANT    Arquivo de modelagem do sistema simulado pelo PLANTsim. 
          [necessário] [Linguagem de modelagem PLANTsim]

.PRG      Arquivo contendo um programa em linguagem GRAFCET (texto) que executa ações de controle do
          sistema modelado em .PLANT. 
          [opcional] [Linguagem GRAFCET]

.SIM      Arquivo contendo uma sequência de eventos que definem os estados do sistema modelado em .PLANT. 
          [opcional] [Linguagem de eventos do PLANTsim]
