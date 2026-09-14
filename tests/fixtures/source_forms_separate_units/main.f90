program forms
implicit none
integer :: value
! ' " ; & < > ? \ @ # { } [ ] | ~ ^
include 'initial.inc'
call add_fixed(value)
if (value /= 37) stop 1
call after_end(value)
if (value /= 43) stop 2
print '(A)', 'FORMS'
end program forms

subroutine after_end(value)
implicit none
integer, intent(out) :: value
value = 43
end subroutine after_end
