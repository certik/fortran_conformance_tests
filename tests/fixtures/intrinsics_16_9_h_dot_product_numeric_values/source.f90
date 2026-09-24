! rule: S16.9.73-003
! covers: DOT_PRODUCT-integer-sum-products
! covers: DOT_PRODUCT-real-sum-products
! covers: DOT_PRODUCT-numeric-zero-size-zero
program i169h_dot_product_numeric_values
  implicit none
  integer :: checks
  integer :: zi(0), zj(0)
  checks = 0
  call require('DOT_PRODUCT integer sum of products', dot_product([1, 2, 3], [2, 3, 4]) == 20, checks)
  call require('DOT_PRODUCT real sum of products exact', dot_product([1.0, 2.0], [4.0, 8.0]) == 20.0, checks)
  call require('DOT_PRODUCT zero-size numeric vectors give zero with nonzero companion', &
       dot_product(zi, zj) == 0 .and. dot_product([2], [3]) == 6, checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DOT PRODUCT NUMERIC VALUES OK'
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
end program i169h_dot_product_numeric_values
