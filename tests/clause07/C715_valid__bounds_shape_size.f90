! rule: C715
! covers: lbound-first ubound-first shape-first size-first
! evidence: positive-control
program c715_bounds_shape_size
    implicit none
    integer :: actual(-1:0, 4:6) = 7
    integer :: seen = -1
    call probe(actual, seen)
    if (seen /= 6) error stop 'size'
contains
    subroutine probe(x, observed)
        type(*), intent(in) :: x(-2:, 0:)
        integer, intent(out) :: observed
        if (any(lbound(x) /= [-2, 0])) error stop 'lower-bounds'
        if (any(ubound(x) /= [-1, 2])) error stop 'upper-bounds'
        if (any(shape(x) /= [2, 3])) error stop 'shape'
        if (size(x, dim=2) /= 3) error stop 'extent'
        observed = size(x)
    end subroutine
end program
