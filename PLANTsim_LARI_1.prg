# GRAFCET program
#

# step <space> number
# action <space> type <space> actions ---> only one per line
# transition <space> to <space> logic_expression
#
# Examples:
#  action begin tk3.fv.active = true #comentário
#  action delay 5 tk3.fv.active 
#  action if tk3.lsh.active then tk3.fv.active
#   action timed 10 tk3.fv.active
#  action end if not tk3.lsh.active or tk3.lvl.pv>15 then tk3.fv.active = false
#  transition from 0 to 10,20 if not tk3.lsh.active or tk2.lvl.pv >= 90

step 0 true
    action cont pip23.fv23.active=true, tk2.fc02.active=false, tk2.lvl.sp=100, sis.fv02.active=true
    transition from 0 to 10,20 if tk2.lvl>45
step 10 
    action cont tk3.mix3.active=false
    transition from 10 to 30 if tk2.lvl<45
step 20 
    action cont pip23.fv23.active=true, sis.fv23.active=true, sis.fv63.active=true, sis.fv02.active=true
    transition from 20 to 30 if tk3.lvl<=20
step 30 
    action cont tk3.mix3.active=false, sis.fv02.active = true
    transition from 30 to 40 if tk3.lvl>40
step 40 
    action cont tk2.fc02.active=true , tk3.lvl.sp=4, sis.fv02.active=true, pip23.fv23.active=false
    transition from 10,20,40 to 0 if tk2.lvl>=47
