! rule: S16.9.112-004
! covers: IPARITY-mask-pack-equivalence
! covers: IPARITY-all-false-mask-zero
program i169n_iparity_mask_values
  implicit none
  integer :: checks
  integer :: a(3)
  logical :: mask_some(3), mask_none(3)
  checks = 0
  a = [14, 13, 8]
  mask_some = [.true., .false., .true.]
  mask_none = [.false., .false., .false.]
  call require('IPARITY with MASK equals packed ARRAY reduction', &
       same_bits(iparity(a, mask=mask_some), iparity(pack(a, mask_some))), checks)
  call require('IPARITY all-false MASK gives zero', &
       popcnt(iparity(a, mask=mask_none)) == 0 .and. popcnt(iparity(a, mask=mask_some)) > 0, checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N IPARITY MASK VALUES OK'
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
  logical function same_bits(a, b)
    integer, intent(in) :: a, b
    integer :: k
    same_bits = .true.
    do k = 0, bit_size(a) - 1
      if (btest(a, k) .neqv. btest(b, k)) same_bits = .false.
    end do
  end function same_bits
end program i169n_iparity_mask_values
