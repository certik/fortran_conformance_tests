! rule: R609
! covers: defined-binary-op
! evidence: positive-control
module r609_binary_m
    implicit none
    interface operator (.combine.)
        module procedure combine_integers
    end interface
contains
    integer function combine_integers(left, right) result(value)
        integer, intent(in) :: left, right
        value = 10 * left + right
    end function combine_integers
end module r609_binary_m

program defined_binary
    use r609_binary_m
    implicit none
    integer :: left, right, result

    left = 4
    right = 7
    result = left .combine. right
    if (result /= 47) error stop 1
end program defined_binary
