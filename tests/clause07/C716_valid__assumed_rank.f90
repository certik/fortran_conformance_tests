! rule: C716
! covers: assumed-rank-scalar assumed-rank-array
! evidence: positive-control
program c716_assumed_rank
    implicit none
    integer :: scalar = 7, array(2, 3) = 5
    integer :: seen = -1
    call forward(scalar, seen)
    if (seen /= 0) error stop 'scalar-effective-rank'
    seen = -1
    call forward(array, seen)
    if (seen /= 2) error stop 'array-effective-rank'
contains
    subroutine forward(x, observed)
        type(*), intent(in) :: x(..)
        integer, intent(out) :: observed
        call sink(x, observed)
    end subroutine
    subroutine sink(x, observed)
        type(*), intent(in) :: x(..)
        integer, intent(out) :: observed
        observed = rank(x)
    end subroutine
end program
