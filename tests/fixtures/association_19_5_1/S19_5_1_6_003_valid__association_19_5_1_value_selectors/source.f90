! rule: S19.5.1.6-003
! covers: expression-selector-value-association vector-subscript-section-value-association selector-value-evaluated-before-block
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_value_selectors
  implicit none
  integer :: x, i, arr(3), idx(2), expr_seen, vector_seen(2), timed_seen, checks
  x = 5
  i = 1
  arr = [10, 20, 30]
  idx = [3, 1]
  expr_seen = -11
  vector_seen = [-12, -13]
  timed_seen = -14
  checks = 0
  associate (a => x + 1)
    expr_seen = a
    x = 100
    call expect_equal(a, 6, 'expression selector value unchanged')
  end associate
  associate (a => arr(idx))
    vector_seen = a
    arr(3) = 99
    call expect_equal(a(1), 30, 'vector subscript first value unchanged')
    call expect_equal(a(2), 10, 'vector subscript second value unchanged')
  end associate
  associate (a => arr(i) + 5)
    timed_seen = a
    i = 2
    arr(1) = 88
    call expect_equal(a, 15, 'selector value evaluated before block')
  end associate
  call expect_equal(expr_seen, 6, 'expression selector recorded value')
  call expect_equal(vector_seen(1), 30, 'vector selector recorded first')
  call expect_equal(vector_seen(2), 10, 'vector selector recorded second')
  call expect_equal(timed_seen, 15, 'timed selector recorded value')
  call expect_equal(checks, 8, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 VALUE SELECTORS OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_value_selectors
