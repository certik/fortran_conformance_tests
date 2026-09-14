! rule: S6.3.2.2-004
! covers: select-rank
! evidence: positive-control
program select_rank_separator
  implicit none
  call check(7)
contains
  subroutine check(value)
    integer, intent(in) :: value(..)
    select rank(value)
    rank(0)
      if (value /= 7) stop 1
    rank default
      stop 2
    end select
  end subroutine
end program
