program p
implicit none
integer :: value
character(len=40) :: rec
namelist /grp/ value
rec='&grp value=7 /'; value=-1
read(unit=rec, nml=grp)
if(value/=7) error stop 1
end program p
