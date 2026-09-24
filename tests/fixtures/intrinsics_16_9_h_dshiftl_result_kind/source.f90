! rule: S16.9.75-002
! covers: DSHIFTL-result-kind-from-I-or-J
program i169h_dshiftl_result_kind
  implicit none
  integer, parameter :: alt_ik = merge(8, 4, kind(0) /= 8)
  integer(kind=alt_ik) :: i, j
  integer :: checks
  checks = 0
  i = 1_alt_ik; j = 2_alt_ik
  call require('dshiftl result kind follows integer operand', &
       kind(dshiftl(i, j, 1)) == kind(i) .and. kind(dshiftl(z'03', j, 1)) == kind(j), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DSHIFTL RESULT KIND OK'
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
end program i169h_dshiftl_result_kind
