! rule: C714
! covers: scalar-dummy
! evidence: positive-control
program c714_scalar
    implicit none
    integer, target :: actual = 7
    integer :: seen = -1
    call probe(actual, seen)
    if (seen /= 0) error stop 'scalar-rank'
contains
    subroutine probe(x, observed)
        type(*), optional, target, intent(inout) :: x
        integer, intent(out) :: observed
        if (.not. present(x)) error stop 'missing-dummy'
        observed = rank(x)
    end subroutine
end program
