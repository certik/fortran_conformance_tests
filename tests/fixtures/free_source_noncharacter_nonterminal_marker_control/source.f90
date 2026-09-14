program noncharacter_marker
implicit none
integer :: value
value = -1
value=1+&
&2
if (value /= 3) error stop 1
end program
