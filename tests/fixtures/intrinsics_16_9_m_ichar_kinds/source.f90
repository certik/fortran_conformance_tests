! rule: S16.9.105-002
! covers: ICHAR-result-integer-kind-from-KIND
! covers: ICHAR-result-default-integer-kind-without-KIND
program i169m_ichar_kinds
  implicit none
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  checks = 0
  call require('ICHAR present KIND selects integer result kind', kind(ichar('A', kind=ik)) == ik, checks)
  call require('ICHAR absent KIND gives default integer kind', kind(ichar('A')) == kind(0), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M ICHAR KINDS OK'
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
end program i169m_ichar_kinds
