! rule: R706
! covers: integer-expression-kind
! evidence: positive-control
! profile: integer-literal-kind-code-decimal10
! standard: f2023
program p
    implicit none
    integer, parameter :: wide = selected_int_kind(18)
    integer(wide), parameter :: selector = kind(0)
    integer(selector + 0_wide) :: a = 13
    if (kind(a) /= kind(0)) error stop 1
    if (a /= 13) error stop 2
end program
