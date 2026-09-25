! rule: S16.9.106-002
! covers: IEOR-result-kind-from-I-or-J
program i169m_ieor_kind
  implicit none
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  checks = 0
  call require('IEOR result kind follows non-BOZ integer operand', &
       kind(ieor(z'01', 3_ik)) == ik .and. kind(ieor(3_ik, z'01')) == ik, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M IEOR KIND OK'
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
end program i169m_ieor_kind
