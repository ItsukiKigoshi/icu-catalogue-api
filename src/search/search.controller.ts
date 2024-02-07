import { Controller, Get } from '@nestjs/common';

@Controller('search')
export class SearchController {
  @Get('hello')
  getHello(): string {
    return 'Hello World!';
  }
}
