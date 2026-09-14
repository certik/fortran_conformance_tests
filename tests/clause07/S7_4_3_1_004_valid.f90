! rule: S7.4.3.1-004
! covers: omitted-selector-kind default-range-five
! evidence: effect
program p
    implicit none
    integer :: value
    integer(kind=kind(0)) :: explicit_value
    value = 99999
    explicit_value = -99999
    if (kind(value) /= kind(0)) error stop 1
    if (kind(value) /= kind(explicit_value)) error stop 2
    if (range(value) < 5) error stop 3
    if (value /= 10000 * 9 + 9999) error stop 4
    if (explicit_value /= 0 - 10000 * 9 - 9999) error stop 5
    call check(value)
contains
    subroutine check(n)
        integer(kind=kind(0)), intent(in) :: n
        if (n /= 99999) error stop 6
    end subroutine
end program
