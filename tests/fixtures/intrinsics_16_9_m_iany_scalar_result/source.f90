! rule: S16.9.101-002
! covers: IANY-result-scalar-without-dim-or-rank-one
program i169m_iany_scalar_result
  implicit none
  integer :: checks
  checks = 0
  call require('IANY result scalar without DIM or rank one DIM', &
       size(shape(iany([1, 2, 4]))) == 0 .and. size(shape(iany([1, 2, 4], dim=1))) == 0, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M IANY SCALAR RESULT OK'
contains
  subroutine require(label, condition, checks)
    character(len=*), intent(in) :: label
    logical, intent(in) :: condition
    integer, intent(inout) :: checks
    if (.not. condition) then
      write(*,'(a)') label
      error stop
    end if
    checks = checks + 1
  end subroutine require
end program i169m_iany_scalar_result
