program integer_literal_kind_code_decimal10
    implicit none
    integer :: reduced, i
    reduced = kind(0)
    if (reduced < 0) error stop 1
    do i = 1, 10
        reduced = reduced / 10
    end do
    if (reduced /= 0) stop 77
end program
