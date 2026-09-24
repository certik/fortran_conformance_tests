program attributes_dimension_grammar
  implicit none
  integer :: r2(2,3)
  integer, parameter :: implied(-2:*) = [10, 20, 30]
  integer, parameter :: shared_star(*) = [5, 7]
  integer :: base(-1:1)
  integer :: checks
  r2 = reshape([1, 2, 3, 4, 5, 6], shape(r2))
  base = [11, 13, 17]
  checks = 0
  call expect_equal(rank(r2), 2, 'explicit rank')
  call expect_equal(size(r2, 1), 2, 'explicit first extent')
  call expect_equal(size(r2, 2), 3, 'explicit second extent')
  call check_assumed_shape(base)
  call check_assumed_size(base)
  call expect_equal(lbound(implied, 1), -2, 'implied lower bound')
  call expect_equal(ubound(implied, 1), 0, 'implied upper bound')
  call expect_equal(implied(-1), 20, 'implied payload')
  call expect_equal(lbound(shared_star, 1), 1, 'shared star lower bound')
  call expect_equal(ubound(shared_star, 1), 2, 'shared star upper bound')
  call expect_equal(shared_star(2), 7, 'shared star payload')
  call expect_equal(checks, 15, 'check total before completion')
  write(*,'(a)') 'ATTRIBUTES DIMENSION GRAMMAR OK'
contains
  subroutine check_assumed_shape(x)
    integer, intent(in) :: x(0:)
    call expect_equal(rank(x), 1, 'assumed-shape rank')
    call expect_equal(lbound(x, 1), 0, 'assumed-shape lower bound')
    call expect_equal(ubound(x, 1), 2, 'assumed-shape upper bound')
  end subroutine
  subroutine check_assumed_size(x)
    integer, intent(in) :: x(0:*)
    call expect_equal(lbound(x, 1), 0, 'assumed-size lower bound')
    call expect_equal(x(0), 11, 'assumed-size first payload')
    call expect_equal(x(2), 17, 'assumed-size last payload')
  end subroutine
  subroutine expect_equal(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ATTR-DIM-GRAMMAR-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
end program attributes_dimension_grammar
