! rule: C715
! covers: rank-first
! evidence: positive-control
program c715_rank
    implicit none
    integer :: scalar = 7, array(2, 3) = 5
    integer :: seen = -1
    call scalar_rank(scalar, seen)
    if (seen /= 0) error stop 'scalar-rank'
    seen = -1
    call array_rank(array, seen)
    if (seen /= 2) error stop 'array-rank'
contains
    subroutine scalar_rank(x, observed)
        type(*), intent(in) :: x
        integer, intent(out) :: observed
        observed = rank(x)
    end subroutine
    subroutine array_rank(x, observed)
        type(*), intent(in) :: x(:, :)
        integer, intent(out) :: observed
        observed = rank(x)
    end subroutine
end program
