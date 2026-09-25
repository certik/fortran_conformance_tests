! rule: S16.9.106-003
! covers: IEOR-boz-converted-as-int-to-other-kind
program i169m_ieor_boz
  implicit none
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer(kind=ik) :: left, right, expect
  integer :: checks
  checks = 0
  left = ieor(z'0F', 10_ik)
  right = ieor(10_ik, z'0F')
  expect = ieor(int(z'0F', kind=ik), 10_ik)
  call require('IEOR BOZ operand is converted as INT to other kind', &
       left == expect .and. right == expect .and. btest(left, 0) .and. btest(left, 2), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M IEOR BOZ OK'
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
end program i169m_ieor_boz
