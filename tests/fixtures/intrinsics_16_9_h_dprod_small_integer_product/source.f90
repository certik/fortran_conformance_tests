! rule: S16.9.74-003
! covers: DPROD-product-approximation
program i169h_dprod_small_integer_product
  implicit none
  integer :: checks
  checks = 0
  call require('DPROD exact small integer-valued product', dprod(-3.0, 2.0) == -6.0d0, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DPROD SMALL INTEGER PRODUCT OK'
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
end program i169h_dprod_small_integer_product
