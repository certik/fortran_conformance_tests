! rule: S16.9.111-003
! covers: IOR-boz-converted-as-int-to-other-kind
program i169n_ior_boz_and_values
  implicit none
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  integer(kind=ik) :: from_left, from_right
  checks = 0
  from_left = ior(z'05', 2_ik)
  from_right = ior(2_ik, z'05')
  call require('IOR BOZ operand is converted like INT to other kind', &
       btest(from_left, 0) .and. btest(from_left, 1) .and. btest(from_left, 2) .and. &
       popcnt(from_left) == 3 .and. btest(from_right, 0) .and. btest(from_right, 1) .and. &
       btest(from_right, 2) .and. popcnt(from_right) == 3, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N IOR BOZ AND VALUES OK'
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
end program i169n_ior_boz_and_values
