! rule: S16.9.102-002
! covers: IBCLR-result-same-kind-as-I
program i169m_ibclr_kind
  implicit none
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  checks = 0
  call require('IBCLR result has same kind as I', kind(ibclr(7_ik, 1)) == ik, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M IBCLR KIND OK'
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
end program i169m_ibclr_kind
