! rule: C714
! covers: assumed-rank-dummy
! evidence: positive-control
program c714_assumed_rank
    implicit none
    integer :: scalar = 7, array(2) = [3, 5]
    integer :: seen = -1
    call probe(scalar, seen)
    if (seen /= 0) error stop 'scalar-effective-rank'
    seen = -1
    call probe(array, seen)
    if (seen /= 1) error stop 'array-effective-rank'
contains
    subroutine probe(x, observed)
        type(*), intent(in) :: x(..)
        integer, intent(out) :: observed
        observed = rank(x)
    end subroutine
end program
