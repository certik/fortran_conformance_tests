! rule: S16.9.101-002
! covers: IANY-result-type-kind-from-array
program i169m_iany_result_kind
  implicit none
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer(kind=ik) :: wide(3)
  integer :: checks
  checks = 0
  wide = [1_ik, 3_ik, 4_ik]
  call require('IANY result kind follows integer ARRAY kind', kind(iany(wide)) == ik, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M IANY RESULT KIND OK'
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
end program i169m_iany_result_kind
