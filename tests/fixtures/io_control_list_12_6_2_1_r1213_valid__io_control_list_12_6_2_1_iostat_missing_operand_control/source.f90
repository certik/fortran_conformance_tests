program p
implicit none
integer :: value
character(len=1) :: rec
rec = '7'
value = -777
read(unit=rec, fmt='(I1)') value
if (value /= 7) error stop 1
end program p
