! rule: S11.1.3.2-001
! covers: block-executes-after-selector-evaluation
program ab1132_eval_block
  implicit none
  integer :: counter, result, inside
  counter=0; result=-1; inside=-2
  associate (value => bump())
    inside=counter
    result=value
  end associate
  if (counter /= 1) then
    write(*,'(a)') 'COUNTER'
    error stop
  end if
  if (inside /= 1) then
    write(*,'(a)') 'INSIDE'
    error stop
  end if
  if (result /= 72) then
    write(*,'(a)') 'RESULT'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS EVAL BLOCK OK'

contains
  integer function bump()
    counter=counter+1
    bump=72
  end function bump
end program ab1132_eval_block
