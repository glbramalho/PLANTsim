# PLANTsim
PLANTsim: a digital twin framework for industrial plants modeling and simulation

PLANTsim was developed to emulate the behaviour of an industrial process. It was
designed to create a digital twin of a didactic industrial process plant used to teach automation and
industrial networks concepts. PLANTsim can be used to demonstrate automation techniques and
develop industrial controller programming and supervisory control skills. This software was
developed in Python and is distributed as an open-source platform to teach industrial
automation concepts and techniques for engineering students.

Keywords: digital twin, industrial automation, process simulation

O PLANTsim foi desenvolvido para simular o comportamento de um processo industrial.
Ele foi projetado para criar um gêmeo digital de uma planta de processo industrial didático usada
para ensinar conceitos de automação e redes industriais. PLANTsim pode ser usado para
demonstrar técnicas de automação e desenvolver programação de controlador industrial e
habilidades de controle de supervisão. Este software foi desenvolvido em Python e é distribuído
como uma plataforma open-source para ensinar conceitos e técnicas de automação industrial para
estudantes de engenharia.

Palavras-chave: gêmeo digital, automação industrial, simulação de processo

Arquivos:
.INI      Arquivo de configuração do PLANTsim. 
          [necessário]
.PLANT    Arquivo de modelagem do sistema simulado pelo PLANTsim. 
          [necessário]
.PRG      Arquivo contendo um programa em linguagem GRAFCET (texto) que executa ações de controle do
          sistema modelado em .PLANT. 
          [opcional]
.SIM      Arquivo contendo uma sequência de eventos que definem os estados do sistema modelado em .PLANT. 
          [opcional]
