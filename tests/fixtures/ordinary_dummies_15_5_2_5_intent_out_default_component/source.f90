! rule: S15.5.2.5-023
! covers: intent-out-default-initialized-direct-component-exception
! evidence: effect
! standard: f2023
module ordinary_dummy_intent_m
  implicit none
  type :: defaulted
    integer :: keep = 17
    integer :: fill
  end type
contains
  subroutine observe_defaulted_out(x, keep_seen)
    type(defaulted), intent(out) :: x
    integer, intent(out) :: keep_seen
    keep_seen = x%keep
    x%keep = 23
    x%fill = 45
  end subroutine
end module
program ordinary_dummy_intent
  use ordinary_dummy_intent_m
  implicit none
  integer :: checks = 0, keep_seen = -2
  type(defaulted) :: item
  item%keep = 101; item%fill = 102
  call observe_defaulted_out(item, keep_seen)
  call expect_equal(keep_seen, 17, 'intent out default component entry')
  call expect_equal(item%keep, 23, 'intent out default component return')
  call expect_equal(item%fill, 45, 'intent out fill component return')
  call expect_equal(checks, 3, 'check count')
  write(*,'(a)') 'ORDINARY DUMMY INTENT OK'
contains
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'OD15525-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
