! rule: S16.9.96-003
! covers: HUGE-integer-model-upper-bound
! covers: HUGE-integer-distinguishes-kinds
program i169l_huge_integer_model
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  integer :: model_default
  integer(kind=ik) :: model_wide
  checks = 0
  model_default = integer_huge_model(0)
  model_wide = integer_huge_model_kind(0_ik)
  call require('HUGE integer equals r**q minus one model', &
       huge(0) == model_default .and. huge(0_ik) == model_wide, checks)
  call require('HUGE integer model distinguishes selected kinds', &
       digits(0_ik) /= digits(0) .and. huge(0_ik) == model_wide, checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L HUGE INTEGER MODEL OK'
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
  integer function integer_huge_model(x) result(model)
    integer, intent(in) :: x
    integer :: k, r
    model = 0
    r = radix(x)
    do k = 1, digits(x)
      model = model * r + (r - 1)
    end do
  end function integer_huge_model
  integer(kind=ik) function integer_huge_model_kind(x) result(model)
    integer(kind=ik), intent(in) :: x
    integer :: k
    integer(kind=ik) :: r
    model = 0_ik
    r = int(radix(x), kind=ik)
    do k = 1, digits(x)
      model = model * r + (r - 1_ik)
    end do
  end function integer_huge_model_kind
end program i169l_huge_integer_model
