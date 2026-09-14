program label_blank
    implicit none
    integer :: value
    value = 7
10 continue
    if (value /= 7) error stop 1
end program
