program label_comment
    implicit none
    integer :: value
    value = 7
10 continue ! Commentary supplies no statement.
    if (value /= 7) error stop 1
end program
