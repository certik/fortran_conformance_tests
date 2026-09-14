! rule: C603
! covers: all-zero-definition
! case: one-digit
program zero_one
    implicit none
0   continue ! {error C603 one-digit}
end program
! case: two-digits
program zero_two
    implicit none
00  continue ! {error C603 two-digits}
end program
! case: three-digits
program zero_three
    implicit none
000 continue ! {error C603 three-digits}
end program
! case: four-digits
program zero_four
    implicit none
0000 continue ! {error C603 four-digits}
end program
! case: five-digits
program zero_five
    implicit none
00000 continue ! {error C603 five-digits}
end program
