! rule: C715
! covers: is-contiguous-first
! evidence: positive-control
program c715_contiguous
    implicit none
    integer :: actual(3) = [2, 3, 5]
    logical :: seen = .false.
    call probe(actual, seen)
    if (.not. seen) error stop 'contiguous-dummy'
contains
    subroutine probe(x, observed)
        type(*), contiguous, intent(in) :: x(:)
        logical, intent(out) :: observed
        observed = is_contiguous(x)
    end subroutine
end program
