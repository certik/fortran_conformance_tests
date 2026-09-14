! rule: S7.4.3.1-001
! covers: default-method selected-method inquiry-connections inventory-membership
! evidence: effect
! standard: f2023
program p
    use iso_fortran_env, only: integer_kinds
    implicit none
    integer, parameter :: wide = selected_int_kind(18)
    integer :: default_value, quotient, decimal_range
    integer(wide) :: selected_value, wide_quotient
    if (size(integer_kinds) < 1) error stop 1
    if (.not. any(integer_kinds == kind(0))) error stop 2
    if (.not. any(integer_kinds == wide)) error stop 3
    default_value = -17
    selected_value = 23_wide
    if (kind(selected_value) /= wide) error stop 4
    if (default_value /= 0 - 10 - 7) error stop 5
    if (selected_value /= 20_wide + 3_wide) error stop 6
    quotient = huge(default_value)
    decimal_range = 0
    do while (quotient >= 10)
        quotient = quotient / 10
        decimal_range = decimal_range + 1
    end do
    if (range(default_value) /= decimal_range) error stop 7
    wide_quotient = huge(selected_value)
    decimal_range = 0
    do while (wide_quotient >= 10_wide)
        wide_quotient = wide_quotient / 10_wide
        decimal_range = decimal_range + 1
    end do
    if (range(selected_value) /= decimal_range) error stop 8
    print *, 'integer_kinds', integer_kinds
    print *, 'default_kind_radix_digits_range', kind(0), radix(0), digits(0), range(0)
    print *, 'default_huge', huge(0)
    print *, 'selected18_kind_radix_digits_range', wide, radix(0_wide), digits(0_wide), range(0_wide)
    print *, 'selected18_huge', huge(0_wide)
end program
