! rule: S6.3.2.2-005
! covers: end-function end-subroutine in-out
! evidence: positive-control
program procedure_spellings
  implicit none
  integer :: value
  value = 1
  call compact(value)
  if (value /= 3) stop 1
  call spaced(value)
  if (value /= 6) stop 2
  if (first() /= 7) stop 3
  if (second() /= 9) stop 4
contains
  subroutine compact(n)
    integer, intent(inout) :: n
    n = n + 2
  endsubroutine compact
  subroutine spaced(n)
    integer, intent(in out) :: n
    n = n + 3
  end subroutine spaced
  integer function first()
    first = 7
  endfunction first
  integer function second()
    second = 9
  end function second
end program
