! rule: S16.9.101-004
! covers: IANY-mask-pack-equivalence
! covers: IANY-all-false-mask-uses-zero-identity
program i169m_iany_mask
  implicit none
  integer :: arr(4), checks
  logical :: mask(4), false_mask(4)
  checks = 0
  arr = [3, 8, 1, 4]
  mask = [.true., .false., .true., .false.]
  false_mask = .false.
  call require('IANY MASK is equivalent to PACK selection', &
       iany(arr, mask=mask) == iany(pack(arr, mask)) .and. btest(iany(arr, mask=mask), 0), checks)
  call require('IANY all-false MASK uses zero identity', &
       popcnt(iany(arr, mask=false_mask)) == 0 .and. popcnt(iany(arr, mask=mask)) /= 0, checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M IANY MASK OK'
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
end program i169m_iany_mask
