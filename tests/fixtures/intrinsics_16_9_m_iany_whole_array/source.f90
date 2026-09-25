! rule: S16.9.101-003
! covers: IANY-bitwise-or-all-elements
! covers: IANY-zero-size-identity-zero-bits
program i169m_iany_whole_array
  implicit none
  integer :: a(3), zero(0), r, checks
  checks = 0
  a = [1, 3, 4]
  r = iany(a)
  call require('IANY whole array is bitwise OR of elements', &
       btest(r, 0) .and. btest(r, 1) .and. btest(r, 2) .and. popcnt(r) == 3, checks)
  call require('IANY zero-size array gives zero bits', &
       popcnt(iany(zero)) == 0 .and. popcnt(iany(a)) /= 0, checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M IANY WHOLE ARRAY OK'
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
end program i169m_iany_whole_array
