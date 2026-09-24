program expr_conditional_selection
  implicit none
  integer :: checks, calls, seen, x
  checks=0
  calls=0; seen=0
  x = 10 * (.true. ? branch(1,2) : branch(9,3))
  if (x /= 20 .or. calls /= 1 .or. seen /= 1) error stop 'ECS:primary'
  checks=checks+1
  calls=0; seen=0
  x = (.true. ? branch(2,11) : branch(8,22))
  if (x /= 11 .or. calls /= 1 .or. seen /= 2) error stop 'ECS:true'
  checks=checks+1
  calls=0; seen=0
  x = (.false. ? branch(3,11) : branch(4,22))
  if (x /= 22 .or. calls /= 1 .or. seen /= 4) error stop 'ECS:false'
  checks=checks+1
  calls=0; seen=0
  x = (.false. ? branch(5,10) : .true. ? branch(6,20) : branch(7,30))
  if (x /= 20 .or. calls /= 1 .or. seen /= 6) error stop 'ECS:nested'
  checks=checks+1
  if (checks /= 4) error stop 'ECS:checks'
  write(*,'(a)') 'EXPRESSIONS CONDITIONAL SELECTION OK'
contains
  integer function branch(tag, value)
    integer, intent(in) :: tag, value
    calls = calls + 1
    seen = tag
    branch = value
  end function branch
end program expr_conditional_selection
