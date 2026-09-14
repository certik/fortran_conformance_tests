program bare_ampersand
implicit none
integer :: value
value = -1
!& ! commentary
value = 7
if (value /= 7) error stop 1
end program
