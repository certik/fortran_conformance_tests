! rule: C709
! covers: typeof-declaration
! evidence: positive-control
! standard: f2023
program c709_typeof_prefix
    implicit none
    integer :: seed = 3
    if (make() /= 7) error stop 'result'
contains
    function make() result(value)
        typeof(seed) :: value
        value = 7
    end function
end program
