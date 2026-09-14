program mixed_form
implicit none
integer :: value
value = 1
     & + 2
if (value /= 3) stop 1
end program
