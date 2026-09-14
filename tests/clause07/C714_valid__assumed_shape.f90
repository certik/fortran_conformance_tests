! rule: C714
! covers: assumed-shape-dummy
! evidence: positive-control
program c714_assumed_shape
    implicit none
    integer :: actual(2, 3) = 7
    integer :: seen = -1
    call probe(actual, seen)
    if (seen /= 6) error stop 'assumed-shape-size'
contains
    subroutine probe(x, observed)
        type(*), intent(in) :: x(:, :)
        integer, intent(out) :: observed
        if (rank(x) /= 2) error stop 'assumed-shape-rank'
        observed = size(x)
    end subroutine
end program
