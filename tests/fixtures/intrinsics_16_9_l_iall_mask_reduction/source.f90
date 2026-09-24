! rule: S16.9.99-004
! covers: IALL-mask-pack-equivalence
! covers: IALL-all-false-mask-uses-zero-size-identity
program i169l_iall_mask_reduction
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer :: checks
  integer :: values(4), k
  logical :: mask(4), refmask(4), none(4), one(4)
  checks = 0
  values = [15, 14, 13, 11]
  mask = [.false., .true., .false., .true.]
  refmask = [.false., .true., .false., .true.]
  none = .false.
  one = [.false., .true., .false., .false.]
  call require('IALL MASK is equivalent to reducing PACK', &
       all([(btest(iall(values, mask=mask), k) .eqv. &
              btest(iall(pack(values, refmask)), k), k = 0, 4)]), checks)
  call require('IALL all-false MASK uses zero-size identity', &
       all([(btest(iall(values, mask=none), k) .eqv. btest(not(0), k), k = 0, 7)]) .and. &
       .not. btest(iall(values, mask=one), bit_size(0)-1), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L IALL MASK REDUCTION OK'
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
  integer function type_code_integer(x)
    integer, intent(in) :: x
    type_code_integer = 1
  end function type_code_integer
  integer function type_code_real(x)
    real, intent(in) :: x
    type_code_real = 2
  end function type_code_real
end program i169l_iall_mask_reduction
