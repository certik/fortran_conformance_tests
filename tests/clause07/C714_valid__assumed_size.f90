! rule: C714
! covers: assumed-size-dummy
! evidence: positive-control
program c714_assumed_size
    implicit none
    integer :: actual(2, 3) = 7
    integer :: seen = -1
    call probe(actual, seen)
    if (seen /= 2) error stop 'assumed-size-rank'
contains
    subroutine probe(x, observed)
        type(*), intent(in) :: x(2, *)
        integer, intent(out) :: observed
        observed = rank(x)
    end subroutine
end program
